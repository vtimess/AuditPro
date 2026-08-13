from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "sys_user"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    openid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    unionid: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)
    real_name: Mapped[str] = mapped_column(String(64), default="微信用户", nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    mobile: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    org_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    role_code: Mapped[str] = mapped_column(String(32), default="ordinary_user", nullable=False)
    role_name: Mapped[str] = mapped_column(String(32), default="普通用户", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False, index=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
