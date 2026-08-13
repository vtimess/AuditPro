from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv


BACKEND_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_ROOT / ".env")


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "港务审计小程序 API")
    app_env: str = os.getenv("APP_ENV", "development")
    app_secret: str = os.getenv("APP_SECRET", "auditpro-development-only-secret")
    token_expire_minutes: int = int(os.getenv("TOKEN_EXPIRE_MINUTES", "10080"))
    api_prefix: str = "/api/v1"

    wechat_app_id: str = os.getenv("WECHAT_APP_ID", "wxaa5ec51c6c3a5d36")
    wechat_app_secret: str = os.getenv("WECHAT_APP_SECRET", "")
    dev_wechat_openid: str = os.getenv("DEV_WECHAT_OPENID", "dev_auditpro_user")

    db_host: str = os.getenv("DB_HOST", "59.110.62.226")
    db_port: int = int(os.getenv("DB_PORT", "34409"))
    db_user: str = os.getenv("DB_USER", "aliyun_zx")
    db_password: str = os.getenv("DB_PASSWORD", "")
    db_name: str = os.getenv("DB_NAME", "audit_pro")
    db_charset: str = os.getenv("DB_CHARSET", "utf8mb4")
    database_url_override: str = os.getenv("DATABASE_URL", "")

    file_root: str = os.getenv("FILE_ROOT", "/data/auditpro/uploads")
    auto_create_tables: bool = _as_bool(os.getenv("AUTO_CREATE_TABLES"), True)
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:3000")

    @property
    def debug(self) -> bool:
        return self.app_env.lower() != "production"

    @property
    def database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override
        password = quote_plus(self.db_password)
        return (
            f"mysql+pymysql://{quote_plus(self.db_user)}:{password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            f"?charset={self.db_charset}"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.app_env == "production" and settings.app_secret == "auditpro-development-only-secret":
        raise RuntimeError("生产环境必须通过 APP_SECRET 设置独立的令牌签名密钥")
    return settings


settings = get_settings()
