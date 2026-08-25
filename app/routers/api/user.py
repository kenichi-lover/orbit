from typing import Annotated

from fastapi import (
    APIRouter, Depends, File, HTTPException, Query, UploadFile, status
)
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from app.config.database import get_session
from app.dependencies.auth import get_current_user, require_superuser
from app.models.user import User
from app.schemas.user_schema import (
    UserPublic,
    UserUpdate,
    UserPasswordUpdate,
)
from app.services import user_service
from app.utils.security import hash_password, verify_password

router = APIRouter(prefix="/users", tags=["users"])


# ═══════════════════════════════════════════════════
# 简单响应 / 请求模型（建议后续抽到 app/schemas/common.py）
# ═══════════════════════════════════════════════════

class MessageResponse(SQLModel):
    message: str


class AvatarResponse(SQLModel):
    success: bool = True
    avatar_url: str


class AdminPasswordReset(SQLModel):
    """管理员强制重置密码请求体"""
    new_password: str = Field(..., min_length=8, max_length=128)


# ═══════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════

def _check_user_access(current_user: User, target_user_id: int) -> None:
    """校验权限：管理员可访问任意用户，普通用户仅能访问自己。"""
    if not current_user.is_superuser and current_user.id != target_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )


# ═══════════════════════════════════════════════════
# /users/me  当前用户操作
# ═══════════════════════════════════════════════════

@router.get("/me", response_model=UserPublic)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """获取当前登录用户信息。"""
    return current_user


@router.post("/me/avatar", response_model=AvatarResponse)
async def upload_my_avatar(
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """上传当前用户头像，保存到 static/avatars 并返回可访问 URL。"""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file uploaded",
        )

    file_data = await file.read()
    avatar_url = await user_service.save_user_avatar(
        current_user, file_data, file.filename
    )
    await session.commit()
    return AvatarResponse(avatar_url=avatar_url)


@router.patch("/me", response_model=UserPublic)
async def update_me(
    data: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """更新当前登录用户信息，禁止自行提权。"""
    if data.is_superuser is not None and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify superuser status",
        )

    updated_user = await user_service.update_user(session, current_user, data)
    return updated_user


@router.patch("/me/password", response_model=MessageResponse)
async def update_my_password(
    data: UserPasswordUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """修改当前登录用户密码，需提供旧密码验证。"""
    if not verify_password(data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password",
        )

    new_hashed = hash_password(data.new_password)
    await user_service.update_password(session, current_user, new_hashed)
    return MessageResponse(message="Password updated successfully")


# ═══════════════════════════════════════════════════
# 用户列表 & 详情（管理员 / 本人）
# ═══════════════════════════════════════════════════

@router.get("", response_model=list[UserPublic])
async def list_users(
    current_user: Annotated[User, Depends(require_superuser)],
    session: Annotated[AsyncSession, Depends(get_session)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """获取用户列表（仅管理员）。"""
    return await user_service.get_users(session, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """获取指定用户信息。管理员可查看任意用户，普通用户仅可查看自己。"""
    _check_user_access(current_user, user_id)

    user = await user_service.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


# ═══════════════════════════════════════════════════
# 管理员操作
# ═══════════════════════════════════════════════════

@router.patch("/{user_id}", response_model=UserPublic)
async def update_user(
    user_id: int,
    data: UserUpdate,
    current_user: Annotated[User, Depends(require_superuser)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """管理员更新任意用户信息。"""
    user = await user_service.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # 防止管理员误删自己权限导致锁死
    if user.id == current_user.id and data.is_superuser is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revoke your own admin privileges",
        )

    return await user_service.update_user(session, user, data)


@router.patch("/{user_id}/password", response_model=MessageResponse)
async def admin_reset_password(
    user_id: int,
    data: AdminPasswordReset,
    current_user: Annotated[User, Depends(require_superuser)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """管理员强制重置用户密码。"""
    user = await user_service.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await user_service.update_password(session, user, hash_password(data.new_password))
    return MessageResponse(
        message=f"Password for user {user.username} has been reset"
    )


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    current_user: Annotated[User, Depends(require_superuser)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """管理员禁用用户（软删除）。"""
    user = await user_service.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself",
        )

    await user_service.deactivate_user(session, user)
    return MessageResponse(message=f"User {user.username} has been deactivated")
