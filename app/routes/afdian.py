import httpx
import logging
from fastapi import APIRouter, Request, HTTPException, Query
from ..config import settings
from ..db.database import get_db
from ..billing.credits import add_credits, update_plan

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/billing")

AFDIAN_PLANS = {
    "starter": {"credits": 5000, "price": 19, "title": "DataClean Starter 套餐"},
    "pro": {"credits": 10000, "price": 49, "title": "DataClean Pro 套餐"},
    "business": {"credits": 50000, "price": 149, "title": "DataClean Business 套餐"},
}


@router.get("/afdian/checkout")
async def afdian_checkout(plan: str = Query(...), token: str = Query(...)):
    """返回爱发电支付链接（用户通过爱发电主页支付，Webhook回调发放额度）。"""
    logger.info(f"AFDian checkout: plan={plan}")

    if plan not in AFDIAN_PLANS:
        raise HTTPException(400, f"无效套餐: {plan}")

    if not settings.afdian_user_id:
        raise HTTPException(500, "爱发电用户 ID 未配置 (AFDIAN_USER_ID 未设置)")

    db = get_db()
    if db is None:
        raise HTTPException(500, "数据库不可用")

    user_resp = db.table("users").select("id, email").eq("auth_token", token).execute()
    if not user_resp.data:
        raise HTTPException(401, "登录状态已过期")

    user = user_resp.data[0]
    plan_info = AFDIAN_PLANS[plan]

    afdian_url = f"https://afdian.net/a/{settings.afdian_user_id}"

    return {
        "afdian_url": afdian_url,
        "plan": plan,
        "price": plan_info["price"],
        "credits": plan_info["credits"],
        "title": plan_info["title"],
        "user_id": user["id"],
        "message": f"请在爱发电主页支付 ¥{plan_info['price']}，支付成功后额度将自动到账。",
    }


@router.post("/afdian/confirm")
async def afdian_confirm(plan: str = Query(...), token: str = Query(...)):
    """用户确认已通过爱发电支付，手动触发额度发放（供Webhook延迟时使用）。"""
    logger.info(f"AFDian confirm: plan={plan}")

    if plan not in AFDIAN_PLANS:
        raise HTTPException(400, f"无效套餐: {plan}")

    db = get_db()
    if db is None:
        raise HTTPException(500, "数据库不可用")

    user_resp = db.table("users").select("id").eq("auth_token", token).execute()
    if not user_resp.data:
        raise HTTPException(401, "登录状态已过期")

    user = user_resp.data[0]
    plan_info = AFDIAN_PLANS[plan]

    credits = plan_info["credits"]
    await add_credits(user["id"], credits)
    await update_plan(user["id"], plan)

    logger.info(f"AFDian manual confirm: user={user['id']}, plan={plan}, credits={credits}")
    return {
        "status": "success",
        "credits_added": credits,
        "plan": plan,
    }
