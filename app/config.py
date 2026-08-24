from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    env: str = "development"
    app_name: str = "DataClean API"
    app_version: str = "0.1.0"
    api_prefix: str = "/v1"

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_key: str = ""

    # Redis
    redis_url: str = ""

    # Rate limits
    rate_limit_qps_free: int = 2
    rate_limit_qps_paid: int = 30
    rate_limit_daily_free: int = 50
    rate_limit_daily_paid: int = 3000

    # LemonSqueezy
    lemonsqueezy_api_key: str = ""
    lemonsqueezy_webhook_secret: str = ""
    lemonsqueezy_store_id: str = ""

    # Security
    api_key_secret: str = "change-this"
    cors_origins: str = "http://localhost:3000"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()


def get_cors_origins() -> list[str]:
    return [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
