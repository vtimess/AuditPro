from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.security import create_access_token
from app.dependencies import DbSession
from app.models.user import User
from app.schemas.auth import LoginResult, WechatLoginRequest
from app.schemas.common import ApiResponse
from app.schemas.user import UserView
from app.services.wechat import WechatLoginError, exchange_code


router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/wechat-login", response_model=ApiResponse[LoginResult])
def wechat_login(payload: WechatLoginRequest, db: DbSession) -> ApiResponse[LoginResult]:
    try:
        identity = exchange_code(payload.code)
    except WechatLoginError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    user = db.scalar(select(User).where(User.openid == identity["openid"]))
    if user is None:
        user = User(
            openid=str(identity["openid"]),
            unionid=identity.get("unionid"),
            real_name=payload.nickname or "微信用户",
            avatar_url=payload.avatar_url,
            role_code="ordinary_user",
            role_name="普通用户",
        )
        db.add(user)
    else:
        if payload.nickname:
            user.real_name = payload.nickname
        if payload.avatar_url:
            user.avatar_url = payload.avatar_url
    user.last_login_at = datetime.now()
    db.commit()
    db.refresh(user)

    result = LoginResult(
        access_token=create_access_token(user.id, user.openid),
        user=UserView.model_validate(user),
    )
    return ApiResponse(data=result)
