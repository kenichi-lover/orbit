from fastapi import (
    APIRouter, Depends, HTTPException, Request, Response, status)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError  # 导入数据库异常

from app.config.settings import settings
from app.config.database import get_session
from app.schemas.user_schema import (
    UserCreateSchema, UserLoginSchema, UserReadSchema, TokenResponse
    )
from app.services import user_service
from app.utils.limiter import limiter
from app.utils.jwt import create_access_token
from app.utils.security import verify_password
from app.dependencies.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

# --- 优化点：抽取 Cookie 配置 ---
# 根据 Debug 模式统一配置 Cookie 安全属性
IS_DEBUG = getattr(settings, "DEBUG", False)
COOKIE_SECURE = not IS_DEBUG
COOKIE_SAMESITE = "lax" if IS_DEBUG else "none"

def set_auth_cookie(response: Response, access_token: str):
    """辅助函数：设置认证 Cookie"""
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        max_age=60 * 24 * 7,  # 7 天
        path="/",
        samesite=COOKIE_SAMESITE,
    )

def clear_auth_cookie(response: Response):
    """辅助函数：清除认证 Cookie"""
    # 注意：删除 Cookie 时 path, secure, samesite 等参数必须与设置时完全一致，否则可能删除失败
    response.delete_cookie(
        key="access_token",
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        httponly=True,
        path="/"  # 建议显式指定 path
    )

async def _authenticate_user(
    session: AsyncSession,
    username: str,
    password: str,
) -> User:
    """校验用户名、密码和账号状态。"""
    user = await user_service.get_user_by_username(session, username)
    
    # --- 优化点：防止时序攻击 ---
    # 如果用户不存在，也执行一次 verify_password，模拟密码验证耗时，防止攻击者通过响应时间猜解用户名
    if not user:
        verify_password(password, "dummy_hash_to_prevent_timing_attack")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
        
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )
    return user

@router.post("/register", response_model=UserReadSchema, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    data: UserCreateSchema,
    session: AsyncSession = Depends(get_session),
):
    """
    用户注册。
    优化：移除了显式的 check existing，直接尝试插入。
    利用数据库 IntegrityError 捕获冲突，减少一次查询并解决并发问题。
    """
    try:
        user = await user_service.create_user(
            session=session,
            username=data.username,
            email=data.email,
            password=data.password,
        )
        return user
    except IntegrityError:
        # 这里可以根据具体的数据库错误信息进一步判断是 username 冲突还是 email 冲突
        # 如果需要精细提示，可以在 create_user 内部捕获并抛出自定义异常
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or Email already registered",
        )

@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    response: Response,
    data: UserLoginSchema,
    session: AsyncSession = Depends(get_session),
):
    """用户登录，返回 JWT token。"""
    user = await _authenticate_user(session, data.username, data.password)

    access_token = create_access_token(subject=str(user.id))
    
    # --- 优化点：使用辅助函数 ---
    set_auth_cookie(response, access_token)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        username=user.username,
    )

@router.post("/logout")
async def logout(response: Response):
    """登出，清除 Cookie。"""
    # --- 优化点：使用辅助函数 ---
    clear_auth_cookie(response)
    return {"message": "Logged out"}

@router.get("/me", response_model=UserReadSchema)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """获取当前登录用户信息。"""
    return current_user
