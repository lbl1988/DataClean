import httpx
import logging
from fastapi import APIRouter, Request, HTTPException, Query
from ..config import settings
from ..db.database import get_db
from ..billing.credits import add_credits, update_plan

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/billing")

AFDIAN_PLANS = {
    "starter": {"plan_id": "starter", "credits": 5000, "price": 19, "title": "DataClean Starter 套餐"},
    "pro": {"plan_id": "pro", "credits": 10000, "price": 49, "title": "DataClean Pro 套餐"},
    "business": {"plan_id": "business", "credits": 50000, "price": 149, "title": "DataClean Business 套餐"},
}


@router.get("/afdian/checkout")
async def afdian_checkout(plan: str = Query(...), token: str = Query(...)):
    """创建爱发电订单，返回支付链接和二维码。"""
    logger.info(f"AFDian checkout: plan={plan}")

    if plan not in AFDIAN_PLANS:
        raise HTTPException(400, f"无效套餐: {plan}")

    if not settings.afdian_token:
        raise HTTPException(500, "爱发电 API 未配置 (AFDIAN_TOKEN 未设置)")

    db = get_db()
    if db is None:
        raise HTTPException(500, "数据库不可用")

    user_resp = db.table("users").select("id, email").eq("auth_token", token).execute()
    if not user_resp.data:
        raise HTTPException(401, "登录状态已过期")

    user = user_resp.data[0]
    plan_info = AFDIAN_PLANS[plan]

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.afdian.com/open/api/order/create",
                headers={
                    "Authorization": f"Bearer {settings.afdian_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "plan_id": plan_info["plan_id"],
                    "title": plan_info["title"],
                    "amount": plan_info["price"] * 100,
                    "target_type": "shop",
                    "target_id": settings.afdian_user_id,
                    "extra": f"user_id={user['id']}&plan={plan}",
                    "notify_uri": "https://dataclean-x4jc.onrender.com/v1/webhook/afdian",
                },
            )
    except httpx.ConnectError as e:
        logger.error(f"AFDian connection error: {e}")
        raise HTTPException(502, "无法连接到爱发电支付服务")
    except httpx.TimeoutException:
        raise HTTPException(504, "爱发电支付服务响应超时")
    except Exception as e:
        logger.error(f"AFDian request failed: {e}")
        raise HTTPException(500, f"支付请求失败: {str(e)[:100]}")

    if resp.status_code not in (200, 201):
        logger.error(f"AFDian API error: status={resp.status_code}, body={resp.text[:500]}")
        raise HTTPException(502, "创建爱发电订单失败")

    data = resp.json()
    if data.get("code") != 0:
        raise HTTPException(502, f"爱发电订单错误: {data.get('msg', '未知错误')}")

    order_data = data.get("data", {})
    return {
        "order_id": order_data.get("order_id"),
        "pay_url": order_data.get("pay_url"),
        "qr_code": order_data.get("qr_code"),
        "plan": plan,
        "price": plan_info["price"],
        "credits": plan_info["credits"],
    }


@router.get("/afdian/query")
async def afdian_query_order(order_id: str = Query(...)):
    """查询爱发电订单状态。"""
    if not settings.afdian_token:
        raise HTTPException(500, "爱发电 API 未配置")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"https://api.afdian.com/open/api/order/query/{order_id}",
                headers={"Authorization": f"Bearer {settings.afdian_token}"},
            )
    except Exception as e:
        logger.error(f"AFDian query failed: {e}")
        raise HTTPException(500, f"查询订单失败: {str(e)[:100]}")

    if resp.status_code != 200:
        raise HTTPException(502, "查询订单失败")

    data = resp.json()
    if data.get("code") != 0:
        return {"status": "unknown", "msg": data.get("msg", "")}

    order = data.get("data", {})
    return {
        "status": order.get("status", "unknown"),
        "paid": order.get("status") == "paid",
        "order_id": order.get("order_id"),
    }
