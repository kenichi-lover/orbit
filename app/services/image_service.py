from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from typing import Sequence

from PIL import Image as PILImage
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import col

from app.config.settings import settings
from app.models.image import Image
from app.schemas.image_schema import ImageCreate, ImagePublic, ImageSearchParams, ImageUpdate
from app.utils.enums import Category


# ==================== 配置 ====================

STATIC_DIR = Path(settings.STATIC_DIR)
IMAGES_DIR = Path(settings.IMAGES_DIR)

THUMBNAIL_SIZE = (settings.THUMBNAIL_WIDTH, settings.THUMBNAIL_HEIGHT)
MAX_FILE_SIZE = settings.MAX_IMAGE_FILE_SIZE
ALLOWED_EXTENSIONS = {f".{ext.lower()}" for ext in settings.ALLOWED_IMAGE_EXTENSIONS}

# 软删除清理保留天数
SOFT_DELETE_RETENTION_DAYS = settings.SOFT_DELETE_RETENTION_DAYS


# ==================== 内部工具 ====================

def _ensure_dirs(path: Path) -> None:
    """确保目录存在"""
    path.mkdir(parents=True, exist_ok=True)


def _generate_storage_path(original_filename: str) -> tuple[str, str]:
    """
    生成存储路径和唯一文件名。
    目录结构: static/images/{year}/{month}/{uuid}.{ext}
    """
    ext = Path(original_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".jpg"

    now = datetime.now(timezone.utc)
    file_name = f"{uuid.uuid4().hex}{ext}"
    year_month = now.strftime("%Y/%m")

    relative_path = f"images/{year_month}/{file_name}"
    return relative_path, file_name


def _get_full_path(relative_path: str | None) -> Path | None:
    """相对路径 → 绝对路径"""
    if not relative_path:
        return None
    return STATIC_DIR / relative_path


async def _write_file_async(file_data: bytes, full_path: Path) -> None:
    """异步写文件（线程池包装同步 I/O）"""
    loop = asyncio.get_running_loop()
    _ensure_dirs(full_path.parent)
    await loop.run_in_executor(None, full_path.write_bytes, file_data)


async def _delete_file_async(relative_path: str | None) -> None:
    """异步删文件，失败静默"""
    if not relative_path:
        return
    full_path = _get_full_path(relative_path)
    if not full_path:
        return

    def _remove() -> None:
        full_path.unlink(missing_ok=True)

    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _remove)
    except Exception:
        pass


def _get_image_dimensions(file_data: bytes) -> tuple[int, int] | None:
    """获取图片宽高"""
    try:
        with PILImage.open(BytesIO(file_data)) as img:
            return img.size  # type: ignore[return-value]
    except Exception:
        return None


def _detect_mime_type(file_data: bytes) -> str:
    """检测 MIME 类型，优先 python-magic，降级到 Pillow"""
    try:
        import magic  # type: ignore[import-untyped]
        return magic.from_buffer(file_data, mime=True)
    except ImportError:
        pass

    try:
        with PILImage.open(BytesIO(file_data)) as img:
            mapping = {
                "JPEG": "image/jpeg",   # ✅ 修正: images/ → image/
                "PNG": "image/png",
                "GIF": "image/gif",
                "WEBP": "image/webp",
            }
            format_key = img.format or "JPEG"
            return mapping.get(format_key.upper(), "image/webp")
    except Exception:
        return "image/webp"


async def _generate_thumbnail(relative_path: str) -> str | None:
    """生成缩略图，返回缩略图相对路径，失败返回 None"""
    full_path = _get_full_path(relative_path)
    if not full_path or not full_path.exists():
        return None

    thumb_name = f"thumb_{Path(relative_path).name}"
    thumb_relative = str(Path(relative_path).parent / thumb_name)
    thumb_full = _get_full_path(thumb_relative)
    if not thumb_full:
        return None

    def _process() -> str:
        with PILImage.open(full_path) as img:
            img.thumbnail(THUMBNAIL_SIZE, PILImage.Resampling.LANCZOS)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            _ensure_dirs(thumb_full.parent)
            img.save(thumb_full, "JPEG", quality=85, optimize=True)
        return thumb_relative

    try:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _process)
    except Exception:
        return None


def _not_deleted():
    """软删除过滤条件复用"""
    return col(Image.is_deleted) == False  # noqa: E712


# ==================== 对外 Service API ====================

async def upload_image(
    session: AsyncSession,
    *,
    file_data: bytes,
    original_filename: str,
    author_id: int,                   
    meta: ImageCreate | None = None, # ✅ 模块 3: 使用 ImageCreate schema
    generate_thumb: bool = True,
) -> Image:
    """上传图片并创建数据库记录"""

    # 1. 基础校验
    if len(file_data) > MAX_FILE_SIZE:
        raise ValueError(f"文件大小超过 {MAX_FILE_SIZE / 1024 / 1024:.0f}MB 限制")

    # 2. 生成唯一路径
    relative_path, file_name = _generate_storage_path(original_filename)

    # 3. 保存原图
    full_path = _get_full_path(relative_path)
    if full_path is None:
        raise ValueError("无法生成文件存储路径")
    await _write_file_async(file_data, full_path)

    # 4. 生成缩略图
    thumb_relative: str | None = None
    if generate_thumb:
        thumb_relative = await _generate_thumbnail(relative_path)

    # 5. 提取元数据
    dimensions = _get_image_dimensions(file_data)
    width, height = dimensions if dimensions else (None, None)

    # 6. 合并用户传入的元信息
    title = meta.title if meta else None
    description = meta.description if meta else None
    alt_text = meta.alt_text if meta else None
    category = meta.category if meta else Category.GALLERY
    tags = meta.tags if meta else []

    # 7. 入库
    image = Image(
        original_filename=original_filename,
        file_name=file_name,
        relative_path=relative_path,
        thumbnail_relative_path=thumb_relative,
        file_size=len(file_data),
        mime_type=_detect_mime_type(file_data),
        width=width,
        height=height,
        title=title,
        description=description,
        alt_text=alt_text,
        author_id=author_id,          # ✅ 模块 1
        category=category,        # ✅ 模块 3: 枚举
        tags=tags,                # ✅ 模块 2: list[str]
    )
    session.add(image)
    await session.commit()
    await session.refresh(image)
    return image


async def get_image_by_id(
    session: AsyncSession,
    image_id: int,
    include_deleted: bool = False,
) -> Image | None:
    stmt = select(Image).where(col(Image.id) == image_id)
    if not include_deleted:
        stmt = stmt.where(_not_deleted())
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_image_by_file_name(
    session: AsyncSession,
    file_name: str,
    include_deleted: bool = False,
) -> Image | None:
    stmt = select(Image).where(col(Image.file_name) == file_name)
    if not include_deleted:
        stmt = stmt.where(_not_deleted())
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_images_by_user(
    session: AsyncSession,
    *,
    author_id: int | None = None,   
    skip: int = 0,
    limit: int = 20,
    include_deleted: bool = False,
) -> tuple[Sequence[Image], int]:
    """获取图片列表（分页），user_id=None 时返回全部"""
    where_clauses = []
    if not include_deleted:
        where_clauses.append(_not_deleted())
    if author_id is not None:
        where_clauses.append(Image.author_id == author_id)

    # 总数
    count_stmt = select(func.count()).select_from(Image)
    if where_clauses:
        count_stmt = count_stmt.where(*where_clauses)
    total_count = (await session.execute(count_stmt)).scalar_one() or 0

    # 分页
    stmt = (
        select(Image)
        .options(selectinload(Image.author))
        .order_by(col(Image.created_at).desc())
        .offset(skip)
        .limit(limit)
    )
    if where_clauses:
        stmt = stmt.where(*where_clauses)

    items = (await session.execute(stmt)).scalars().all()
    return items, total_count


async def update_image_meta(
    session: AsyncSession,
    image: Image,
    data: ImageUpdate,               # ✅ 模块 3: ImageUpdateSchema → ImageUpdate
) -> Image:
    """更新图片元数据（部分更新），不涉及文件替换"""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(image, field, value)

    session.add(image)
    await session.commit()
    await session.refresh(image)
    return image


async def delete_image(
    session: AsyncSession,
    image: Image,
    hard_delete: bool = False,
) -> None:
    """
    删除图片
    - hard_delete=False: 软删除（保留文件，可恢复）
    - hard_delete=True:  硬删除（删文件 + 删记录）
    """
    if hard_delete:
        await _delete_file_async(image.relative_path)
        await _delete_file_async(image.thumbnail_relative_path)
        await session.delete(image)
    else:
        image.is_deleted = True
        image.deleted_at = datetime.now(timezone.utc)
        session.add(image)

    await session.commit()


async def cleanup_deleted_images(session: AsyncSession) -> int:
    """清理已软删除超过 N 天的图片（定时任务调用）"""
    cutoff = datetime.now(timezone.utc) - timedelta(days=SOFT_DELETE_RETENTION_DAYS)
    stmt = select(Image).where(
        col(Image.is_deleted) == True,  # noqa: E712
        col(Image.deleted_at) <= cutoff,
    )
    images = (await session.execute(stmt)).scalars().all()

    count = 0
    for img in images:
        await _delete_file_async(img.relative_path)
        await _delete_file_async(img.thumbnail_relative_path)
        await session.delete(img)
        count += 1

    if count:
        await session.commit()
    return count


# ==================== 搜索功能 ====================

async def search_images(
    session: AsyncSession,
    params: ImageSearchParams,       # ✅ 模块 6: 散列参数 → 对象
    include_deleted: bool = False,
) -> tuple[Sequence[Image], int]:
    """
    搜索图片（关键词 + 分类 + 标签 + 用户，分页）
    ✅ 模块 2: tags 使用 PG ARRAY @> contains 替代 LIKE
    """
    where_clauses: list = []
    if not include_deleted:
        where_clauses.append(_not_deleted())

    # 关键词搜索：标题或描述模糊匹配
    if params.q and params.q.strip():
        kw = f"%{params.q.strip()}%"
        where_clauses.append(
            or_(
                col(Image.title).ilike(kw),
                col(Image.description).ilike(kw),
            )
        )

    # ✅ 模块 3: 分类筛选（枚举直接比较）
    if params.category is not None:
        where_clauses.append(Image.category == params.category)

    # ✅ 模块 2: 标签筛选 — PG ARRAY contains
    # tags 列是 ARRAY(String)，用 .contains([tag]) 生成 SQL: tags @> ARRAY['tag']
    if params.tag and params.tag.strip():
        where_clauses.append(col(Image.tags).contains([params.tag.strip().lower()]))

    # ✅ 模块 1: 用户筛选（user_id）
    if params.user_id is not None:
        where_clauses.append(Image.author_id == params.user_id)

    # 总数
    count_stmt = select(func.count()).select_from(Image)
    if where_clauses:
        count_stmt = count_stmt.where(*where_clauses)
    total_count = (await session.execute(count_stmt)).scalar_one() or 0

    # 分页查询
    stmt = (
        select(Image)
        .order_by(col(Image.created_at).desc())
        .offset(params.skip)
        .limit(params.limit)
    )
    if where_clauses:
        stmt = stmt.where(*where_clauses)

    items = (await session.execute(stmt)).scalars().all()
    return items, total_count


# ==================== URL / 路径工具 ====================

def get_image_url(relative_path: str | None) -> str | None:
    """相对路径 → 对外访问 URL"""
    if not relative_path:
        return None
    return f"/static/{relative_path}"


def get_image_full_path(relative_path: str | None) -> Path | None:
    """获取绝对路径（用于直接发送文件或做进一步处理）"""
    return _get_full_path(relative_path)



def image_to_public(img: Image) -> ImagePublic:
    """将 Image ORM 对象转为公共响应格式。

    所有路由统一调用此函数，禁止在路由层手写转换逻辑。
    """

    # ── 入口统一断言：DB 查出的记录主键/必填字段不应为 None ──
    if img.id is None:
        raise ValueError(f"Image 缺少主键，无法序列化: {img}")
    if img.relative_path is None:
        raise ValueError(f"Image 缺少 relative_path: id={img.id}")

    # ── URL 生成：主图 URL 失败直接报错，缩略图允许为 None ──
    url = get_image_url(img.relative_path)
    if not url:
        raise ValueError(f"无法生成图片 URL: relative_path={img.relative_path}")

    thumbnail_url = (
        get_image_url(img.thumbnail_relative_path)
        if img.thumbnail_relative_path
        else None
    )

    # ── author 处理 ──
    author_name = None
    if img.author and not getattr(img.author, "is_anonymous", False):
        author_name = img.author.username

    return ImagePublic(
        id=img.id,
        url=url,
        thumbnail_url=thumbnail_url,
        title=img.title,
        description=img.description,
        alt_text=img.alt_text,
        category=img.category,
        tags=img.tags or [],
        original_filename=img.original_filename,
        file_size=img.file_size,
        mime_type=img.mime_type,
        width=img.width,
        height=img.height,
        author_name=author_name,
        created_at=img.created_at,
        updated_at=img.updated_at,
    )