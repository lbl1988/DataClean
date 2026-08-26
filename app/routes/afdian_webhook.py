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

AFDIAN_PLAN_PRICES = {
    "starter": 19.00,
    "pro": 49.00,
    "business": 149.00,
}


@router.post("/webhook/afdian")
async def afdian_webhook(request: Request):
    """爱发电 Webhook 处理器。
    
    爱发电 Webhook 格式:
    {
      "ec": 200,
      "em": "ok",
      "data": {
        "type": "order",
        "order": {
          "out_trade_no": "...",
          "user_id": "...",
          "plan_id": "...",
          "total_amount": "5.00",
          "status": 2,
          ...
        }
      }
    }
    """
    body = await request.body()

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid JSON body")

    event_data = data.get("data", {})
    event_type = event_data.get("type", "")

    if event_type != "order":
        return {"ec": 200, "em": "ok"}

    order = event_data.get("order", {})
    out_trade_no = order.get("out_trade_no", "")
    user_id = order.get("user_id", "")
    plan_id = order.get("plan_id", "")
    status = order.get("status", 0)
    total_amount = float(order.get("total_amount", 0))

    if status != 2:
        logger.info(f"AFDian webhook: order {out_trade_no} status={status}, ignoring")
        return {"ec": 200, "em": "ok"}

    from ..db.database import get_db
    db = get_db()
    if db is None:
        return {"ec": 500, "em": "database unavailable"}

    existing = (
        db.table("payments")
        .select("id")
        .eq("afdian_order_id", out_trade_no)
        .execute()
    )
    if existing.data:
        logger.info(f"AFDian webhook: order {out_trade_no} already processed")
        return {"ec": 200, "em": "ok"}

    plan = _match_plan_by_amount(total_amount)
    if plan == "free":
        logger.warning(f"AFDian webhook: unknown amount {total_amount}, cannot match plan")
        return {"ec": 200, "em": "ok"}

    credits = AFDIAN_PLAN_CREDITS.get(plan, 0)

    user_resp = db.table("users").select("id").eq("id", user_id).execute()
    if not user_resp.data:
        logger.warning(f"AFDian webhook: user {user_id} not found")
        return {"ec": 200, "em": "user not found"}

    await add_credits(user_id, credits)
    await update_plan(user_id, plan)

    db.table("payments").insert({
        "user_id": user_id,
        "afdian_order_id": out_trade_no,
        "amount": total_amount,
        "credits_purchased": credits,
        "plan": plan,
        "status": "paid",
    }).execute()

    logger.info(f"AFDian webhook: order {out_trade_no} processed, plan={plan}, credits={credits}")
    return {"ec": 200, "em": "ok"}


def _match_plan_by_amount(amount: float) -> str:
    for plan, price in AFDIAN_PLAN_PRICES.items():
        if abs(amount - price) < 0.01:
            return plan
    return "free"
