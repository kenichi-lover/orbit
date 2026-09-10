from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_session
from app.dependencies.auth import require_superuser
from app.models.user import User
from app.schemas.user_schema import (
    AdminPasswordReset,
    MessageResponse,
    UserPublic,
    UserUpdate,
)
from app.services import user_service
from app.utils.security import hash_password

router = APIRouter(prefix="/admin/users", tags=["users", "admin"])


async def _get_user_or_404(session: AsyncSession, user_id: int) -> User:
    """公共查找逻辑，避免每个端点重复 404 判断。"""
    user = await user_service.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.get("", response_model=list[UserPublic])
async def list_users(
    session: Annotated[AsyncSession, Depends(get_session)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """获取用户列表。"""
    return await user_service.get_users(session, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(
    user_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """获取指定用户信息。"""
    return await _get_user_or_404(session, user_id)


@router.patch("/{user_id}", response_model=UserPublic)
async def update_user(
    user_id: int,
    data: UserUpdate,
    current_user: Annotated[User, Depends(require_superuser)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """管理员更新任意用户信息。"""
    user = await _get_user_or_404(session, user_id)
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
    del current_user
    user = await _get_user_or_404(session, user_id)
    await user_service.update_password(session, user, hash_password(data.new_password))
    return MessageResponse(message=f"Password for user {user.username} has been reset")


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    current_user: Annotated[User, Depends(require_superuser)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """管理员禁用用户（软删除）。"""
    user = await _get_user_or_404(session, user_id)
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself",
        )
    await user_service.deactivate_user(session, user)
    return MessageResponse(message=f"User {user.username} has been deactivated")
