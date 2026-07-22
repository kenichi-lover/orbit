import asyncio
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Sequence

from PIL import Image as PILImage
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import DateTime, column, desc, select, func

from app.models.image import Image
from app.schemas.image_schema import ImageUpdateSchema  # 需自行定义，含 title/description/alt_text 等


# ==================== 配置 ====================

STATIC_DIR = Path("static")
IMAGES_DIR = STATIC_DIR / "images"

THUMBNAIL_SIZE = (300, 300)          # 缩略图最大宽高
MAX_FILE_SIZE = 10 * 1024 * 1024     # 10MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


# ==================== 内部工具 ====================

def _ensure_dirs(path: Path) -> None:
    """确保目录存在"""
    path.mkdir(parents=True, exist_ok=True)


def _generate_storage_path(original_filename: str) -> tuple[str, str]:
    """
    生成存储路径和唯一文件名
    返回: (relative_path, file_name)
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
    """相对路径 -> 绝对路径"""
    if not relative_path:
        return None
    return STATIC_DIR / relative_path


async def _write_file_async(file_data: bytes, full_path: Path) -> None:
    """异步写文件（线程池包装同步 I/O）"""
    loop = asyncio.get_event_loop()
    _ensure_dirs(full_path.parent)

    def _write():
        full_path.write_bytes(file_data)

    await loop.run_in_executor(None, _write)


async def _delete_file_async(relative_path: str | None) -> None:
    """异步删文件，失败静默"""
    if not relative_path:
        return
    full_path = _get_full_path(relative_path)
    if not full_path:
        return

    def _remove():
        full_path.unlink(missing_ok=True)

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _remove)
    except Exception:
        pass


def _get_image_dimensions(file_data: bytes) -> tuple[int, int] | None:
    """获取图片宽高"""
    try:
        with PILImage.open(BytesIO(file_data)) as img:
            return img.size
    except Exception:
        return None


def _detect_mime_type(file_data: bytes) -> str:
    """检测 MIME 类型，优先 python-magic，降级到 Pillow"""
    try:
        import magic  # type: ignore
        return magic.from_buffer(file_data, mime=True)
    except ImportError:
        try:
            with PILImage.open(BytesIO(file_data)) as img:
                mapping = {
                    "JPEG": "images/jpeg",
                    "PNG": "images/png",
                    "GIF": "images/gif",
                    "WEBP": "images/webp",
                }
                format_key = img.format or "jpeg"
                return mapping.get(format_key, "images/webp")
        except Exception:
            return "images/jpeg"


async def _generate_thumbnail(relative_path: str) -> str | None:
    """
    生成缩略图
    返回缩略图的相对路径，失败返回 None
    """
    full_path = _get_full_path(relative_path)
    if not full_path or not full_path.exists():
        return None

    thumb_name = f"thumb_{Path(relative_path).name}"
    thumb_relative = str(Path(relative_path).parent / thumb_name)
    thumb_full = _get_full_path(thumb_relative)
    if not thumb_full:
        return None

    def _process():
        with PILImage.open(full_path) as img:
            # 保持比例缩放
            img.thumbnail(THUMBNAIL_SIZE, PILImage.Resampling.LANCZOS)
            # RGBA/P 模式转 RGB 以兼容 JPEG
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(thumb_full, "JPEG", quality=85, optimize=True)
        return thumb_relative

    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _process)
    except Exception:
        # 缩略图生成失败不应阻断主流程
        return None


# ==================== 对外 Service API ====================

async def upload_image(
    session: AsyncSession,
    file_data: bytes,
    original_filename: str,
    user_name: str,
    title: str | None = None,
    description: str | None = None,
    alt_text: str | None = None,
    generate_thumb: bool = True,
) -> Image:
    """
    上传图片并创建数据库记录
    """
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
    thumb_relative = None
    if generate_thumb:
        thumb_relative = await _generate_thumbnail(relative_path)

    # 5. 提取元数据
    dimensions = _get_image_dimensions(file_data)
    width, height = dimensions if dimensions else (None, None)

    # 6. 入库
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
        user_name=user_name,
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
    stmt = select(Image).where(Image.id == image_id)
    if not include_deleted:
        stmt = stmt.where(Image.is_deleted == False)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_image_by_file_name(
    session: AsyncSession,
    file_name: str,
    include_deleted: bool = False,
) -> Image | None:
    stmt = select(Image).where(Image.file_name == file_name)
    if not include_deleted:
        stmt = stmt.where(Image.is_deleted == False)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_images_by_user(
    session: AsyncSession,
    user_name: str | None = None,
    skip: int = 0,
    limit: int = 20,
    include_deleted: bool = False,
) -> tuple[Sequence[Image], int]:
    """
    获取用户图片列表（分页）
    返回: (数据列表, 总条数)
    """
    where_clauses = [Image.user_name == user_name]
    if not include_deleted:
        where_clauses.append(Image.is_deleted == False)

    # 总数
    count_stmt = select(func.count()).select_from(Image).where(*where_clauses)
    total = await session.execute(count_stmt)
    total_count = total.scalar_one() or 0

    # 分页
    stmt = (
        select(Image)
        .where(*where_clauses)
        .order_by(desc(Image.created_at))
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(stmt)
    items = result.scalars().all()
    return items, total_count


async def update_image_meta(
    session: AsyncSession,
    image: Image,
    data: ImageUpdateSchema,
) -> Image:
    """
    更新图片元数据（标题、描述等），不涉及文件替换
    """
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
    """
    清理已软删除超过 N 天的图片（可作为定时任务调用）
    返回实际删除的记录数
    """
    from datetime import timedelta

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    stmt = select(Image).where(
        Image.is_deleted == True,
        column("deleted_at", DateTime) <= cutoff
    )
    result = await session.execute(stmt)
    images = result.scalars().all()

    count = 0
    for img in images:
        await _delete_file_async(img.relative_path)
        await _delete_file_async(img.thumbnail_relative_path)
        await session.delete(img)
        count += 1

    if count:
        await session.commit()
    return count


# ==================== URL / 路径工具 ====================

def get_image_url(relative_path: str | None) -> str | None:
    """相对路径 -> 对外访问 URL"""
    if not relative_path:
        return None
    return f"/static/{relative_path}"


def get_image_full_path(relative_path: str | None) -> Path | None:
    """获取绝对路径（用于直接发送文件或做进一步处理）"""
    return _get_full_path(relative_path)