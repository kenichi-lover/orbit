from typing import List

from fastapi import (
    APIRouter, Depends, HTTPException, Query, status
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_session
from app.dependencies.auth import get_current_user, require_superuser
from app.models.user import User
from app.schemas.user_schema import (
    UserReadSchema,
    UserUpdateSchema,
    UserPasswordUpdateSchema,
)
from app.services import user_service
from app.utils.security import verify_password, hash_password

router = APIRouter(prefix="/users", tags=["users"])


def _check_user_access(current_user: User, target_user_id: int) -> None:
    """校验权限：管理员可访问任意用户，普通用户仅能访问自己。"""
    if not current_user.is_superuser and current_user.id != target_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )


# -----------------------------------------------------------------------------
# /users/me  当前用户操作
# -----------------------------------------------------------------------------

@router.get("/me", response_model=UserReadSchema)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息。"""
    return current_user


@router.patch("/me", response_model=UserReadSchema)
async def update_me(
    data: UserUpdateSchema,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """更新当前登录用户信息（昵称、邮箱等），禁止自行提权。"""
    if getattr(data, "is_admin", None) is not None and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify admin status",
        )

    updated_user = await user_service.update_user(session, current_user, data)
    return updated_user


@router.patch("/me/password")
async def update_my_password(
    data: UserPasswordUpdateSchema,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """修改当前登录用户密码，需提供旧密码验证。"""
    if not verify_password(data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password",
        )

    new_hashed = hash_password(data.new_password)
    await user_service.update_password(session, current_user, new_hashed)
    return {"message": "Password updated successfully"}


# -----------------------------------------------------------------------------
# 用户列表 & 详情（管理员 / 本人）
# -----------------------------------------------------------------------------

@router.get("", response_model=List[UserReadSchema])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session),
):
    """获取用户列表（仅管理员）。"""
    return await user_service.get_users(session, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserReadSchema)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """获取指定用户信息。管理员可查看任意用户，普通用户仅可查看自己。"""
    _check_user_access(current_user, user_id)

    user = await user_service.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


# -----------------------------------------------------------------------------
# 管理员操作
# -----------------------------------------------------------------------------

@router.patch("/{user_id}", response_model=UserReadSchema)
async def update_user(
    user_id: int,
    data: UserUpdateSchema,
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session),
):
    """管理员更新任意用户信息。"""
    user = await user_service.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # 防止管理员误删自己权限导致锁死
    if user.id == current_user.id and getattr(data, "is_superuser", None) is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revoke your own admin privileges",
        )

    return await user_service.update_user(session, user, data)


@router.patch("/{user_id}/password")
async def admin_reset_password(
    user_id: int,
    new_password: str,
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session),
):
    """管理员强制重置用户密码。"""
    user = await user_service.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await user_service.update_password(session, user, hash_password(new_password))
    return {"message": f"Password for user {user.username} has been reset"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session),
):
    """管理员禁用用户（软删除）。"""
    user = await user_service.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself")

    await user_service.deactivate_user(session, user)
    return {"message": f"User {user.username} has been deactivated"}