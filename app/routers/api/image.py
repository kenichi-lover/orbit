from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_session
from app.dependencies.auth import get_current_user
from app.models.image import Image
from app.models.user import User
from app.schemas.image_schema import (
    ImagePublic,
    ImageSearchParams,
    ImageUpdateSchema,
)
from app.services import image_service
from app.services.image_service import get_image_url
from app.utils.enums import Category
from app.utils.limiter import limiter
from app.utils.pagination import PaginationParams

router = APIRouter()


# ==================== 辅助函数 ====================

def _image_to_public(img: Image) -> ImagePublic:
    """将 Image ORM 对象转为公共响应格式"""
    assert img.id is not None, "Image must be persisted before serialization"
    
    return ImagePublic(
        id=img.id,
        url=get_image_url(img.relative_path) or "",
        title=img.title or f"Image {img.id}",
        category=img.category or "Gallery",
        description=img.description or None,
        tags=img.tags or None,
        # 如果是 anonymous 则不在公开接口显示作者名
        author_name=img.user_name if img.user_name != "anonymous" else None,
    )


# ==================== 公开接口 ====================

@router.get("/images", response_model=dict)
async def list_images(
    p: Annotated[PaginationParams, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
    user_name: str | None = None,
):
    """获取图片列表（分页），用于轨道舞台渲染"""
    items, total = await image_service.get_images_by_user(
        session,
        user_name=user_name,
        skip=p.skip,
        limit=p.limit,
    )
    public_items = [_image_to_public(img) for img in items]
    
    safe_limit = p.limit if p.limit > 0 else 1
    total_pages = -(-total // safe_limit) if total > 0 else 0
    
    return {
        "items": [i.model_dump() for i in public_items],
        "total": total,
        "skip": p.skip,
        "limit": p.limit,
        "total_pages": total_pages,
        "has_next": (p.skip + len(public_items)) < total,
        "has_prev": p.skip > 0,
    }


@router.post("/images/upload")
@limiter.limit("10/minute")
async def upload_image(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    file: UploadFile = File(...),
    title: Annotated[str | None, Form()] = None,
    description: Annotated[str | None, Form()] = None,
    alt_text: Annotated[str | None, Form()] = None,
    category: Annotated[Category, Form()] = Category.GALLERY,
    tags: Annotated[str | None, Form()] = None,
    # 【优化点】通过 Depends 注入当前用户，允许为 None (匿名上传)
    current_user: Annotated[Optional[User], Depends(get_current_user)] = None,
):
    """上传图片，支持匿名 + 自动登录"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    # Read the file content
    file_data = await file.read()

    # 【优化点】直接使用注入的用户对象，无需 try-except 手动调用
    user_name = current_user.username if current_user else "anonymous"

    try:
        image = await image_service.upload_image(
            session,
            file_data=file_data,
            original_filename=file.filename,
            user_name=user_name,
            title=title,
            description=description,
            alt_text=alt_text,
            category=category.value,
            tags=tags,
        )
        await session.commit()
        return {
            "success": True,
            "image": _image_to_public(image).model_dump(),
        }
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Upload failed")


@router.get("/search", response_model=dict)
async def search_images(
    params: Annotated[ImageSearchParams, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """搜索图片（关键词 + 分类 + 标签筛选）"""
    items, total = await image_service.search_images(
        session,
        q=params.q,
        category=params.category,
        tag=params.tag,
        user_name=params.user_name,
        skip=params.skip,
        limit=params.limit,
    )
    public_items = [_image_to_public(img) for img in items]
    
    safe_limit = params.limit if params.limit > 0 else 1
    total_pages = -(-total // safe_limit) if total > 0 else 0
    
    return {
        "items": [i.model_dump() for i in public_items],
        "total": total,
        "skip": params.skip,
        "limit": params.limit,
        "total_pages": total_pages,
        "has_next": (params.skip + len(public_items)) < total,
        "has_prev": params.skip > 0,
    }


# ==================== 需要认证 ====================


def _ensure_image_access(image: Image, current_user: User) -> None:
    """校验当前用户是否有权限操作图片。"""
    if current_user.is_superuser:
        return

    if image.user_name == "anonymous":
        raise HTTPException(status_code=403, detail="匿名图片仅允许管理员操作")

    if image.user_name != current_user.username:
        raise HTTPException(status_code=403, detail="无权操作此图片")


@router.post("/images/{image_id}")
async def update_image_meta(
    image_id: int,
    data: ImageUpdateSchema,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """更新图片元数据（标题、描述、分类、标签等）"""
    image = await image_service.get_image_by_id(session, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    _ensure_image_access(image, current_user)

    await image_service.update_image_meta(session, image, data)
    return {"success": True}


@router.delete("/images/{image_id}")
async def delete_image(
    image_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    hard: Annotated[bool, Query()] = False,
):
    """删除图片（软删 / 硬删）"""
    image = await image_service.get_image_by_id(session, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    _ensure_image_access(image, current_user)

    await image_service.delete_image(session, image, hard_delete=hard)
    return {"success": True}