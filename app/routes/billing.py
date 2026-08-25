import httpx
from fastapi import APIRouter, Request, HTTPException, Query
from ..config import settings
from ..db.database import get_db

router = APIRouter(prefix="/v1/billing")

PLAN_VARIANTS = {
    "starter": {"variant_id": "2051245", "credits": 5000, "price": 19},
    "pro": {"variant_id": "2051251", "credits": 10000, "price": 49},
    "business": {"variant_id": "2051252", "credits": 50000, "price": 149},
}


@router.get("/checkout")
async def checkout(plan: str = Query(...), token: str = Query(...)):
    """创建 LemonSqueezy 结账页面并跳转。"""
    if plan not in PLAN_VARIANTS:
        raise HTTPException(400, f"无效套餐: {plan}，可选: pro / business / enterprise")

    if not settings.lemonsqueezy_api_key:
        raise HTTPException(500, "支付服务未配置，请联系管理员")

    lsq_key = settings.lemonsqueezy_api_key.strip()
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
                "Authorization": f"Bearer {lsq_key}",
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
                            "redirect_url": "https://dataclean-x4jc.onrender.com/dashboard?tab=billing",
                        },
                    },
                    "relationships": {
                        "store": {
                            "data": {
                                "type": "stores",
                                "id": "458799",
                            }
                        },
                        "variant": {
                            "data": {
                                "type": "variants",
                                "id": variant_id,
                            }
                        },
                    },
                }
            },
        )

    if resp.status_code not in (200, 201):
        raise HTTPException(500, f"创建支付订单失败: {resp.status_code} - {resp.text[:300]}")

    data = resp.json()
    checkout_url = data.get("data", {}).get("attributes", {}).get("url")
    if not checkout_url:
        raise HTTPException(500, "未获取到支付链接")

    return {"checkout_url": checkout_url}


@router.get("/test-lsq")
async def test_lsq():
    """测试 LemonSqueezy API 连通性。"""
    import traceback
    try:
        if not settings.lemonsqueezy_api_key:
            return {"error": "LEMONSQUEEZY_API_KEY not set", "key_len": 0}

        key = settings.lemonsqueezy_api_key.strip()
        result = {
            "key_prefix": key[:40],
            "key_suffix": key[-20:],
            "key_length": len(key),
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    "https://api.lemonsqueezy.com/v1/products",
                    headers={
                        "Authorization": f"Bearer {key}",
                        "Accept": "application/vnd.api+json",
                    },
                )
            result["lsq_status"] = resp.status_code
            result["lsq_response"] = resp.text[:300] if resp.status_code != 200 else "OK"
        except Exception as e:
            result["lsq_error"] = str(e)
            result["lsq_traceback"] = traceback.format_exc()[:500]

        return result
    except Exception as e:
        return {"fatal_error": str(e), "traceback": traceback.format_exc()[:500]}


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
