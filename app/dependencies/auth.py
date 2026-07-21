from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_session
from app.models.user import User
from app.services.user_service import get_user_by_id
from app.utils.jwt import decode_access_token


security = HTTPBearer(auto_error=False)

# 统一的 401 响应，带标准 header
CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Authentication required",
    headers={"WWW-Authenticate": "Bearer"},
)


async def _get_user_from_token(
    session: AsyncSession,
    token: str | None,
) -> User | None:
    """底层：从 token 解析用户。token 无效或用户不存在时返回 None。"""
    if not token:
        return None

    try:
        payload = decode_access_token(token)
    except ValueError:
        return None

    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        return None

    user = await get_user_by_id(session, user_id)
    if user is None or not user.is_active:
        return None

    return user


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> User:
    """从 JWT token 获取当前登录用户。失败时抛 401/403。"""
    token = credentials.credentials if credentials else request.cookies.get("access_token")
    
    user = await _get_user_from_token(session, token)
    if user is None:
        raise CREDENTIALS_EXCEPTION
    
    return user


async def resolve_user_from_cookie(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> User | None:
    """仅从 cookie 尝试解析当前用户，失败时静默返回 None。适合页面级"可选登录"场景。"""
    token = request.cookies.get("access_token")
    return await _get_user_from_token(session, token)


async def require_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """要求当前用户必须是管理员。"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user