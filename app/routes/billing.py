import httpx
from fastapi import APIRouter, Request, HTTPException, Query
from ..config import settings
from ..db.database import get_db

router = APIRouter(prefix="/v1/billing")

PLAN_VARIANTS = {
    "pro": {"variant_id": "2051277", "credits": 10000, "price": 49},
    "business": {"variant_id": "2051278", "credits": 50000, "price": 199},
    "enterprise": {"variant_id": "2051279", "credits": 200000, "price": 399},
}


@router.get("/checkout")
async def checkout(plan: str = Query(...), token: str = Query(...)):
    """创建 LemonSqueezy 结账页面并跳转。"""
    if plan not in PLAN_VARIANTS:
        raise HTTPException(400, f"无效套餐: {plan}，可选: pro / business / enterprise")

    if not settings.lemonsqueezy_api_key:
        raise HTTPException(500, "支付服务未配置，请联系管理员")

    db = get_db()
    if db is None:
        raise HTTPException(500, "数据库不可用")

    user_resp = db.table("users").select("id, email").eq("auth_token", token).execute()
    if not user_resp.data:
        raise HTTPException(401, "无效 token，请重新登录")

    user = user_resp.data[0]
    variant_id = PLAN_VARIANTS[plan]["variant_id"]

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            "https://api.lemonsqueezy.com/v1/checkouts",
            headers={
                "Authorization": f"Bearer {settings.lemonsqueezy_api_key}",
                "Accept": "application/vnd.api+json",
                "Content-Type": "application/vnd.api+json",
            },
            json={
                "data": {
                    "type": "checkouts",
                    "attributes": {
                        "checkout_data": {
                            "email": user.get("email", ""),
                            "custom": {
                                "user_id": user["id"],
                                "plan": plan,
                            },
                        },
                        "product_options": {
                            "redirect_url": f"https://dataclean-x4jc.onrender.com/dashboard?tab=billing",
                        },
                    },
                    "relationships": {
                        "variant": {
                            "data": {
                                "type": "variants",
                                "id": variant_id,
                            }
                        }
                    },
                }
            },
        )

    if resp.status_code not in (200, 201):
        raise HTTPException(500, f"创建支付订单失败: {resp.status_code}")

    data = resp.json()
    checkout_url = data.get("data", {}).get("attributes", {}).get("url")
    if not checkout_url:
        raise HTTPException(500, "未获取到支付链接")

    return {"checkout_url": checkout_url}


@router.get("/balance")
async def get_balance_api(token: str = Query(...)):
    """查询当前用户额度和套餐。"""
    db = get_db()
    if db is None:
        raise HTTPException(500, "数据库不可用")

    user_resp = db.table("users").select("plan, credits_remaining, credits_total").eq("auth_token", token).execute()
    if not user_resp.data:
        raise HTTPException(401, "无效 token")

    record = user_resp.data[0]
    return {
        "plan": record.get("plan", "free"),
        "credits_remaining": record.get("credits_remaining", 0),
        "credits_total": record.get("credits_total", 0),
    }
