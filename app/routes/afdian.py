import logging
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
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
    """获取支付信息。"""
    logger.info(f"AFDian checkout: plan={plan}")

    if plan not in AFDIAN_PLANS:
        raise HTTPException(400, f"无效套餐: {plan}")

    db = get_db()
    if db is None:
        raise HTTPException(500, "数据库不可用")

    user_resp = db.table("users").select("id, email").eq("auth_token", token).execute()
    if not user_resp.data:
        raise HTTPException(401, "登录状态已过期")

    user = user_resp.data[0]
    plan_info = AFDIAN_PLANS[plan]

    return {
        "plan": plan,
        "price": plan_info["price"],
        "credits": plan_info["credits"],
        "title": plan_info["title"],
        "user_id": user["id"],
        "message": f"请扫码支付 ¥{plan_info['price']}，支付后提交申请，管理员审核通过后额度到账。",
    }


@router.post("/afdian/confirm")
async def afdian_confirm(
    plan: str = Query(...), 
    token: str = Query(...),
    payment_method: str = Query("wechat"),
):
    """用户提交支付申请，创建待审核订单。"""
    logger.info(f"AFDian confirm: plan={plan}")

    if plan not in AFDIAN_PLANS:
        raise HTTPException(400, f"无效套餐: {plan}")

    if payment_method not in ["wechat", "alipay"]:
        raise HTTPException(400, "无效的支付方式")

    db = get_db()
    if db is None:
        raise HTTPException(500, "数据库不可用")

    user_resp = db.table("users").select("id", "email").eq("auth_token", token).execute()
    if not user_resp.data:
        raise HTTPException(401, "登录状态已过期")

    user = user_resp.data[0]
    plan_info = AFDIAN_PLANS[plan]

    order_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    try:
        db.table("payments").insert({
            "id": order_id,
            "user_id": user["id"],
            "amount": plan_info["price"],
            "credits_purchased": plan_info["credits"],
            "plan": plan,
            "status": "pending",
            "afdian_order_id": payment_method,
            "created_at": now,
        }).execute()

        logger.info(f"AFDian order created: {order_id}, user={user['id']}")
        return {
            "status": "pending",
            "order_id": order_id,
            "message": "支付申请已提交，等待管理员审核。审核通过后额度将自动到账。",
            "plan": plan,
            "credits": plan_info["credits"],
        }
    except Exception as e:
        logger.error(f"Failed to create order: {e}")
        raise HTTPException(500, f"创建订单失败: {str(e)}")


@router.get("/afdian/order/{order_id}")
async def get_order_status(order_id: str, token: str = Query(...)):
    """查询订单状态。"""
    db = get_db()
    if db is None:
        raise HTTPException(500, "数据库不可用")

    user_resp = db.table("users").select("id").eq("auth_token", token).execute()
    if not user_resp.data:
        raise HTTPException(401, "登录状态已过期")

    order_resp = db.table("payments").select("*").eq("id", order_id).execute()
    if not order_resp.data:
        raise HTTPException(404, "订单不存在")

    order = order_resp.data[0]
    if str(order["user_id"]) != str(user_resp.data[0]["id"]):
        raise HTTPException(403, "无权查看此订单")

    return {
        "order_id": order["id"],
        "status": order["status"],
        "amount": order["amount"],
        "credits": order["credits_purchased"],
        "plan": order["plan"],
        "created_at": order["created_at"],
    }


@router.post("/afdian/admin/approve")
async def admin_approve(
    order_id: str = Query(...),
    token: str = Query(...),
):
    """管理员审核通过订单（审核通过后额度到账）。"""
    db = get_db()
    if db is None:
        raise HTTPException(500, "数据库不可用")

    user_resp = db.table("users").select("id", "email", "plan").eq("auth_token", token).execute()
    if not user_resp.data:
        raise HTTPException(401, "登录状态已过期")

    # 检查管理员权限（临时：所有登录用户都可以审核，后续可改为只有特定用户）
    user = user_resp.data[0]

    order_resp = db.table("payments").select("*").eq("id", order_id).execute()
    if not order_resp.data:
        raise HTTPException(404, "订单不存在")

    order = order_resp.data[0]
    if order["status"] != "pending":
        raise HTTPException(400, f"订单状态为 {order['status']}，无法审核")

    # 审核通过，发放额度
    try:
        await add_credits(order["user_id"], order["credits_purchased"])
        await update_plan(order["user_id"], order["plan"])

        db.table("payments").update({
            "status": "completed",
            "updated_at": datetime.now().isoformat(),
        }).eq("id", order_id).execute()

        logger.info(f"Order {order_id} approved by {user['email']}")
        return {
            "status": "success",
            "order_id": order_id,
            "credits_added": order["credits_purchased"],
            "message": "订单已审核通过，额度已到账",
        }
    except Exception as e:
        logger.error(f"Failed to approve order: {e}")
        raise HTTPException(500, f"审核失败: {str(e)}")


@router.get("/afdian/admin/pending")
async def admin_list_pending(token: str = Query(...)):
    """获取所有待审核订单列表。"""
    db = get_db()
    if db is None:
        raise HTTPException(500, "数据库不可用")

    user_resp = db.table("users").select("id", "email").eq("auth_token", token).execute()
    if not user_resp.data:
        raise HTTPException(401, "登录状态已过期")

    orders = db.table("payments").select("*").eq("status", "pending").order("created_at", desc=True).execute()
    
    result = []
    for order in orders.data:
        result.append({
            "order_id": order["id"],
            "user_id": order["user_id"],
            "amount": order["amount"],
            "credits": order["credits_purchased"],
            "plan": order["plan"],
            "payment_method": order.get("afdian_order_id", ""),
            "created_at": order["created_at"],
        })

    return {"orders": result, "total": len(result)}
