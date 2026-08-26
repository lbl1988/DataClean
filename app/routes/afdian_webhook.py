import hmac
import hashlib
import json
import logging
from fastapi import APIRouter, Request, HTTPException

from ..config import settings
from ..billing.credits import add_credits, update_plan

logger = logging.getLogger(__name__)

router = APIRouter()

AFDIAN_PLAN_CREDITS = {
    "starter": 5000,
    "pro": 10000,
    "business": 50000,
}


@router.post("/webhook/afdian")
async def afdian_webhook(request: Request):
    """爱发电 Webhook 处理器。"""
    body = await request.body()
    signature = request.headers.get("x-signature", "")

    if settings.afdian_webhook_secret:
        expected = hmac.new(
            settings.afdian_webhook_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(401, "Invalid signature")

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid JSON body")

    event_type = data.get("type", "")
    order_data = data.get("data", {})
    order_id = order_data.get("order_id", "")
    extra = order_data.get("extra", "")

    if event_type not in ("order.paid", "order.refunded"):
        return {"status": "ignored", "event_type": event_type}

    from ..db.database import get_db
    db = get_db()
    if db is None:
        return {"status": "database_unavailable"}

    existing = (
        db.table("payments")
        .select("id")
        .eq("afdian_order_id", order_id)
        .execute()
    )
    if existing.data:
        return {"status": "already_processed"}

    user_id = None
    plan = "free"
    if extra:
        for part in extra.split("&"):
            if "=" in part:
                key, value = part.split("=", 1)
                if key == "user_id":
                    user_id = value
                elif key == "plan":
                    plan = value

    if event_type == "order.paid" and user_id:
        credits = AFDIAN_PLAN_CREDITS.get(plan, 0)
        if credits > 0:
            await add_credits(user_id, credits)
            await update_plan(user_id, plan)

        db.table("payments").insert({
            "user_id": user_id,
            "afdian_order_id": order_id,
            "amount": order_data.get("amount", 0),
            "credits_purchased": AFDIAN_PLAN_CREDITS.get(plan, 0),
            "plan": plan,
            "status": "paid",
        }).execute()

    elif event_type == "order.refunded" and user_id:
        db.table("payments").update({
            "status": "refunded",
        }).eq("afdian_order_id", order_id).execute()

    return {"status": "success", "order_id": order_id}
