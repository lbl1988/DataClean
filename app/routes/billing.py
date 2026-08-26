import httpx
import logging
from fastapi import APIRouter, Request, HTTPException, Query
from ..config import settings
from ..db.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/billing")

PLAN_VARIANTS = {
    "starter": {"variant_id": "2051245", "credits": 5000, "price": 19},
    "pro": {"variant_id": "2051251", "credits": 10000, "price": 49},
    "business": {"variant_id": "2051252", "credits": 50000, "price": 149},
}


@router.get("/checkout")
async def checkout(plan: str = Query(...), token: str = Query(...)):
    """创建 LemonSqueezy 结账页面并跳转。"""
    logger.info(f"Checkout request: plan={plan}, token_prefix={token[:20] if token else 'None'}")

    if plan not in PLAN_VARIANTS:
        raise HTTPException(400, f"无效套餐: {plan}，可选: starter / pro / business")

    if not settings.lemonsqueezy_api_key:
        logger.error("LEMONSQUEEZY_API_KEY not configured")
        raise HTTPException(500, "支付服务未配置 (LEMONSQUEEZY_API_KEY 未设置)，请联系管理员")

    lsq_key = settings.lemonsqueezy_api_key.strip()
    db = get_db()
    if db is None:
        logger.error("Database not available")
        raise HTTPException(500, "数据库不可用，请稍后重试")

    user_resp = db.table("users").select("id, email").eq("auth_token", token).execute()
    if not user_resp.data:
        logger.warning(f"Invalid token for checkout")
        raise HTTPException(401, "登录状态已过期，请重新登录")

    user = user_resp.data[0]
    variant_id = PLAN_VARIANTS[plan]["variant_id"]
    logger.info(f"Creating checkout: variant={variant_id}, email={user.get('email')}")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            checkout_payload = {
                "data": {
                    "type": "checkouts",
                    "attributes": {
                        "checkout_data": {
                            "email": user.get("email", ""),
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
            }
            logger.info(f"Checkout payload: {checkout_payload}")
            resp = await client.post(
                "https://api.lemonsqueezy.com/v1/checkouts",
                headers={
                    "Authorization": f"Bearer {lsq_key}",
                    "Accept": "application/vnd.api+json",
                    "Content-Type": "application/vnd.api+json",
                },
                json=checkout_payload,
            )
    except httpx.ConnectError as e:
        logger.error(f"LemonSqueezy connection error: {e}")
        raise HTTPException(502, "无法连接到支付服务，请稍后重试")
    except httpx.TimeoutException as e:
        logger.error(f"LemonSqueezy timeout: {e}")
        raise HTTPException(504, "支付服务响应超时，请稍后重试")
    except Exception as e:
        logger.error(f"LemonSqueezy request failed: {e}")
        raise HTTPException(500, f"支付服务请求失败: {str(e)[:100]}")

    if resp.status_code not in (200, 201):
        error_detail = resp.text[:500] if resp.text else "No response body"
        logger.error(f"LemonSqueezy API error: status={resp.status_code}, body={error_detail}")
        try:
            err_json = resp.json()
            lsq_errors = err_json.get("errors", [])
            if lsq_errors:
                err = lsq_errors[0]
                title = err.get("title", "")
                detail = err.get("detail", "")
                source = err.get("source", {})
                pointer = source.get("pointer", "")
                logger.error(f"LemonSqueezy error: title={title}, detail={detail}, pointer={pointer}")
                
                field_hint = ""
                if "custom" in pointer:
                    field_hint = "自定义数据格式错误，请检查 custom 字段是否为有效的 JSON 对象"
                elif "billing_address" in pointer:
                    field_hint = "账单地址格式错误，请检查 billing_address 字段"
                elif "email" in pointer:
                    field_hint = "邮箱地址格式错误"
                elif "variant" in pointer.lower():
                    field_hint = "套餐 ID 无效或不存在"
                
                error_msg = f"支付服务错误: {detail or title or '未知错误'}"
                if field_hint:
                    error_msg += f" ({field_hint})"
                error_msg += f" [状态码 {resp.status_code}]"
                
                raise HTTPException(502, error_msg)
        except HTTPException:
            raise
        except Exception:
            pass
        raise HTTPException(
            502,
            f"创建支付订单失败 (状态码 {resp.status_code})。"
            f"可能原因：套餐 ID {variant_id} 不存在、API Key 无效或店铺 ID 不匹配。"
            f"响应: {error_detail[:200]}"
        )

    data = resp.json()
    checkout_url = data.get("data", {}).get("attributes", {}).get("url")
    if not checkout_url:
        logger.error(f"No checkout URL in response: {data}")
        raise HTTPException(500, "未获取到支付链接，请稍后重试")

    logger.info(f"Checkout created successfully: plan={plan}, url_prefix={checkout_url[:50]}")
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
