from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import col, select

from app.config.database import get_session
from app.config.settings import settings
from app.dependencies.auth import get_current_user
from app.models.image import Image
from app.models.user import User
from app.schemas.image_schema import (
    ImageCreate,
    ImagePublic,
    ImageSearchParams,
    ImageUpdate,
)
from app.services import image_service
from app.services.image_service import  image_to_public
from app.utils.enums import Category
from app.utils.limiter import limiter
from app.utils.pagination import PaginationParams, PaginatedResponse

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

router = APIRouter()


# ==================== 辅助函数 ====================


async def _get_image_with_author(
    session: AsyncSession,
    image_id: int,
    include_deleted: bool = False,
) -> Image | None:
    """获取图片并预加载作者信息（避免 N+1 查询）"""
    stmt = (
        select(Image)
        .where(col(Image.id) == image_id)
    )
    if not include_deleted:
        stmt = stmt.where(col(Image.is_deleted) == False)  # noqa: E712

    # 预加载作者信息
    stmt = stmt.options(selectinload("author"))   # type: ignore[arg-type]
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


# ==================== 公开接口 ====================

@router.get("/categories")
async def list_categories() -> list[str]:
    """返回所有可用分类枚举值"""
    return [c.value for c in Category]


@router.get("/images", response_model=PaginatedResponse[ImagePublic])
async def list_images(
    p: Annotated[PaginationParams, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
    author_id: int | None = Query(default=None, ge=1),
):
    """获取图片列表（分页），用于轨道舞台渲染"""
    items, total = await image_service.get_images_by_user(
        session,
        author_id=author_id,
        skip=p.skip,
        limit=p.limit,
    )
    public_items = [image_to_public(img) for img in items]

    return PaginatedResponse[ImagePublic].create(
        items=public_items,
        total=total,
        skip=p.skip,
        limit=p.limit,
    )


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
    tags: Annotated[str | None, Form()] = None,  # 逗号分隔字符串
    current_user: Annotated[User | None, Depends(get_current_user)] = None
):

    # ── 鉴权：必须在读文件之前拦截，避免白读大文件 ──
    if current_user is None or current_user.id is None:
        raise HTTPException(status_code=401, detail="请先登录")
    author_id = current_user.id

    """文件名校验"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    # ── MIME 类型校验（客户端声明，不可完全信任，后续可加 python-magic 兜底）──
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file.content_type}，仅允许 {', '.join(sorted(ALLOWED_MIME_TYPES))}",
        )

    # Read the file content
    file_data = await file.read()

    # ── 大小校验（read 之后用实际字节数校验，防伪造 content-length）──
    max_size = settings.MAX_UPLOAD_SIZE
    if len(file_data) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"文件过大，最大允许 {max_size // 1024 // 1024}MB",
        )

    # ✅ 模块 3: 解析 tags 字符串为 list[str]
    tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()] if tags else []

    # ✅ 模块 2: 使用 ImageCreate schema 聚合元信息
    meta = ImageCreate(
        title=title,
        description=description,
        alt_text=alt_text,
        category=category,
        tags=tag_list,
    )

    try:
        image = await image_service.upload_image(
            session,
            file_data=file_data,
            original_filename=file.filename,
            author_id=author_id,
            meta=meta,
        )
        # ✅ 模块 8: 提交事务（service 层已 commit，此处无需重复）
        # 但为确保一致性，可显式 refresh
        await session.refresh(image)
        return {
            "success": True,
            "image": image_to_public(image).model_dump(),
        }
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Upload failed")


@router.get("/search", response_model=PaginatedResponse[ImagePublic])
async def search_images(
    params: Annotated[ImageSearchParams, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """搜索图片（关键词 + 分类 + 标签筛选）"""
    items, total = await image_service.search_images(
        session,
        params=params,
    )
    public_items = [image_to_public(img) for img in items]

    return PaginatedResponse[ImagePublic].create(
        items=public_items,
        total=total,
        skip=params.skip,
        limit=params.limit,
    )

# ==================== 需要认证 ====================

def _ensure_image_access(image: Image, current_user: User) -> None:
    """校验当前用户是否有权限操作图片。"""
    if current_user.is_superuser:
        return

    if image.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此图片")


@router.put("/images/{image_id}")  # ✅ 改用 PUT 更符合 RESTful 语义
async def update_image_meta(
    image_id: int,
    data: ImageUpdate,  # ✅ 模块 2: ImageUpdateSchema → ImageUpdate
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """更新图片元数据（标题、描述、分类、标签等）"""
    image = await _get_image_with_author(session, image_id)
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
    image = await _get_image_with_author(session, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    _ensure_image_access(image, current_user)

    await image_service.delete_image(session, image, hard_delete=hard)
    return {"success": True}
