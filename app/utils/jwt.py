from datetime import datetime, timezone, timedelta
from typing import Any

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from app.config.settings import settings


def create_access_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """生成 JWT access token。
    
    Args:
        subject: Token 主体，通常是用户 ID（会被强制转为字符串）。
        expires_delta: 自定义过期时间，默认从 settings 读取。
        extra_claims: 额外声明（如 roles, permissions）。
    """
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta 
        or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    payload = {
        "sub": str(subject),           # JWT 标准：sub 必须是字符串
        "iat": now,                    # 签发时间
        "exp": expire,                 # 过期时间
        "type": "access",              # Token 类型，防止混用
    }
    if extra_claims:
        payload.update(extra_claims)
    
    return jwt.encode(
        payload,
        settings.SECRET_KEY.get_secret_value(),  # 如果 SECRET_KEY 是 SecretStr
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """解码并验证 JWT access token。验证失败时抛出 ValueError，由调用方处理。"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=[settings.ALGORITHM],
        )
    except ExpiredSignatureError as exc:
        raise ValueError("Token has expired") from exc
    except InvalidTokenError as exc:
        raise ValueError("Invalid token") from exc
    
    # 类型校验：防止 refresh token 或其他 token 被当作 access token 使用
    if payload.get("type") != "access":
        raise ValueError("Invalid token type")
    
    return payload