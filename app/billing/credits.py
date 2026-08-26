from typing import Optional


PLAN_CREDITS = {
    "free": 1000,
    "starter": 5000,
    "pro": 10000,
    "business": 50000,
    "enterprise": 200000,
}


async def deduct_credits(user_id: str, amount: int) -> bool:
    """扣减用户额度。返回True表示成功。"""
    from ..db.database import get_db
    db = get_db()
    if db is None:
        return True

    # 先查当前余额
    response = db.table("users").select("credits_remaining").eq("id", user_id).execute()
    if not response.data:
        return False

    current = response.data[0].get("credits_remaining", 0)
    if current < amount:
        return False

    # 扣减
    db.table("users").update({
        "credits_remaining": current - amount,
    }).eq("id", user_id).execute()

    return True


async def add_credits(user_id: str, amount: int) -> int:
    """增加用户额度。"""
    from ..db.database import get_db
    db = get_db()
    if db is None:
        return 0

    response = db.table("users").select("credits_remaining, credits_total").eq("id", user_id).execute()
    if not response.data:
        return 0

    record = response.data[0]
    new_remaining = (record.get("credits_remaining", 0) or 0) + amount
    new_total = (record.get("credits_total", 0) or 0) + amount

    db.table("users").update({
        "credits_remaining": new_remaining,
        "credits_total": new_total,
    }).eq("id", user_id).execute()

    return new_remaining


async def get_balance(user_id: str) -> dict:
    """查询用户额度。"""
    from ..db.database import get_db
    db = get_db()
    if db is None:
        return {"plan": "free", "credits_remaining": 1000, "credits_total": 1000}

    response = db.table("users").select("plan, credits_remaining, credits_total").eq("id", user_id).execute()
    if not response.data:
        return {"plan": "free", "credits_remaining": 0, "credits_total": 0}

    record = response.data[0]
    return {
        "plan": record.get("plan", "free"),
        "credits_remaining": record.get("credits_remaining", 0),
        "credits_total": record.get("credits_total", 0),
    }


async def update_plan(user_id: str, plan: str) -> dict:
    """更新用户套餐并重置额度。"""
    from ..db.database import get_db
    db = get_db()
    if db is None:
        return {"plan": plan, "credits_remaining": PLAN_CREDITS.get(plan, 1000)}

    credits = PLAN_CREDITS.get(plan, 1000)

    db.table("users").update({
        "plan": plan,
        "credits_remaining": credits,
        "credits_total": credits,
    }).eq("id", user_id).execute()

    return {"plan": plan, "credits_remaining": credits}
