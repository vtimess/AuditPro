from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.user import UserView


class WechatLoginRequest(BaseModel):
    code: str = Field(min_length=1, max_length=128)
    nickname: Optional[str] = Field(default=None, max_length=64)
    avatar_url: Optional[str] = Field(default=None, max_length=500)


class LoginResult(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserView
