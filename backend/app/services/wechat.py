from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import urlopen

from app.core.config import settings


class WechatLoginError(RuntimeError):
    pass


def exchange_code(code: str) -> dict[str, str | None]:
    if not settings.wechat_app_secret:
        if settings.debug:
            return {"openid": settings.dev_wechat_openid, "unionid": None}
        raise WechatLoginError("服务器尚未配置 WECHAT_APP_SECRET")

    params = urlencode(
        {
            "appid": settings.wechat_app_id,
            "secret": settings.wechat_app_secret,
            "js_code": code,
            "grant_type": "authorization_code",
        }
    )
    url = f"https://api.weixin.qq.com/sns/jscode2session?{params}"
    try:
        with urlopen(url, timeout=8) as response:  # noqa: S310 - fixed HTTPS endpoint
            data = json.loads(response.read())
    except Exception as exc:
        raise WechatLoginError("连接微信登录服务失败") from exc

    if data.get("errcode") or not data.get("openid"):
        raise WechatLoginError(data.get("errmsg", "微信登录失败"))
    return {"openid": data["openid"], "unionid": data.get("unionid")}
