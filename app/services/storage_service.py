"""
文件存储服务：负责头像的本地存储、清理与路径生成
"""

import logging
import re
import uuid
from pathlib import Path

from app.config.settings import settings

logger = logging.getLogger(__name__)

STATIC_DIR = Path(settings.STATIC_DIR)
AVATAR_DIR = Path(settings.AVATARS_DIR)
ALLOWED_EXTENSIONS: set[str] = {f".{ext}" for ext in settings.ALLOWED_AVATAR_EXTENSIONS}
MAX_SIZE: int = settings.MAX_AVATAR_SIZE


def _sanitize_filename(name: str) -> str:
    """将任意字符串清理为安全的文件名片段。"""
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "_", name).strip("._")
    return slug or "user"


def _build_avatar_path(user_id: int, username: str, ext: str) -> Path:
    """生成唯一的头像存储路径。"""
    unique = uuid.uuid4().hex[:8]
    safe_name = _sanitize_filename(username)
    return AVATAR_DIR / f"{user_id}_{safe_name}_{unique}{ext}"


def _remove_old_avatars(user_id: int) -> None:
    """删除指定用户的所有旧头像文件（清理孤儿文件）。"""
    if user_id is None:
        return
    for old_file in AVATAR_DIR.glob(f"{user_id}_*"):
        try:
            old_file.unlink(missing_ok=True)
        except OSError:
            logger.warning("无法删除旧头像文件: %s", old_file, exc_info=True)


async def upload_avatar(
    user_id: int,
    username: str,
    file_data: bytes,
    original_filename: str,
) -> str:
    """保存用户头像文件，返回可访问的 URL 路径。

    Args:
        user_id: 用户主键 ID。
        username: 用户名（用于生成文件名）。
        file_data: 文件二进制数据。
        original_filename: 原始文件名（用于提取扩展名）。

    Returns:
        相对 URL，如 ``/static/avatars/1_alice_a3f2c1d8.png``。
    """
    # 1. 校验大小
    if len(file_data) > MAX_SIZE:
        max_mb = MAX_SIZE / (1024 * 1024)
        raise ValueError(f"头像文件过大，最大允许 {max_mb:.0f} MB")

    # 2. 确保目录存在
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)

    # 3. 处理扩展名
    ext = Path(original_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        logger.info("不支持的头像扩展名 '%s'，回退为 .png", ext)
        ext = ".png"

    # 4. 清理旧文件并写入新文件
    _remove_old_avatars(user_id)
    avatar_path = _build_avatar_path(user_id, username, ext)
    
    # 注意：write_bytes 是同步阻塞操作，在高并发场景下建议使用 run_in_threadpool
    avatar_path.write_bytes(file_data)

    logger.info("头像已保存: user_id=%s -> %s", user_id, avatar_path.name)
    return f"/static/avatars/{avatar_path.name}"

