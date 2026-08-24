import hmac
import hashlib
import json
from fastapi import APIRouter, Request, HTTPException

from ..config import settings
from ..billing.credits import add_credits, update_plan

router = APIRouter()

PLAN_CREDITS = {
    "free": 1000,
    "starter": 10000,
    "pro": 50000,
    "business": 200000,
}

VARIANT_PLAN_MAP = {
    "2051277": "starter",
    "2051278": "pro",
    "2051279": "business",
}


@router.post("/webhook/lemonsqueezy")
async def lemonsqueezy_webhook(request: Request):
    """LemonSqueezy Webhook处理器。幂等设计：event_id去重。"""
    body = await request.body()
    signature = request.headers.get("x-signature", "")

    if settings.lemonsqueezy_webhook_secret:
        expected = hmac.new(
            settings.lemonsqueezy_webhook_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(401, "Invalid signature")

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid JSON body")

    event_type = data.get("meta", {}).get("event_type", "")
    event_id = data.get("meta", {}).get("event_id", "")

    from ..db.database import get_db
    db = get_db()
    if db is None:
        return {"status": "database_unavailable"}

    # 幂等检查
    existing = (
        db.table("payments")
        .select("id")
        .eq("lemonsqueezy_payment_id", event_id)
        .execute()
    )
    if existing.data:
        return {"status": "already_processed"}

    attrs = data.get("data", {}).get("attributes", {})
    customer_email = attrs.get("user_email", "")
    variant_id = attrs.get("variant_id", "")

    # 查找用户
    user = None
    if customer_email:
        user_resp = (
            db.table("users")
            .select("id")
            .eq("email", customer_email)
            .execute()
        )
        if user_resp.data:
            user = user_resp.data[0]

    # 处理事件
    if user:
        plan = _match_plan(variant_id)
        user_id = user["id"]

        if event_type in ("order_created", "order_refunded"):
            credits = PLAN_CREDITS.get(plan, 0)
            if credits > 0:
                await add_credits(user_id, credits)
                await update_plan(user_id, plan)
        elif event_type == "subscription_created":
            await update_plan(user_id, plan)
        elif event_type == "subscription_cancelled":
            await update_plan(user_id, "free")

        # 记录支付
        db.table("payments").insert({
            "user_id": user_id,
            "lemonsqueezy_payment_id": event_id,
            "amount": attrs.get("total", 0),
            "credits_purchased": PLAN_CREDITS.get(plan, 0),
            "plan": plan,
            "status": "paid",
        }).execute()

    return {"status": "success", "event_id": event_id}


def _match_plan(variant_id: str) -> str:
    return VARIANT_PLAN_MAP.get(str(variant_id), "free")
