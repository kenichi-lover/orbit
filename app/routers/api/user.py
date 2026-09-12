from typing import Annotated

from fastapi import (
    APIRouter, Depends, File, HTTPException, UploadFile, status
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user_schema import (
    AvatarResponse,
    MessageResponse,
    UserPasswordUpdate,
    UserPublic,
    UserUpdate,
)
from app.services import storage_service, user_service
from app.utils.security import hash_password, verify_password

router = APIRouter(prefix="/users", tags=["users"])


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
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User data corrupted: missing user ID",
        )
    file_data = await file.read()
    avatar_url = await storage_service.upload_avatar(
        user_id=current_user.id,
        username=current_user.username,
        file_data=file_data,
        original_filename=file.filename,
    )
    await user_service.update_avatar_url(session, current_user, avatar_url)
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






