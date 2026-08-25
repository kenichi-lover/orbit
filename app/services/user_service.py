"""
用户服务层：头像管理 + 用户 CRUD
"""

from __future__ import annotations

import logging
import re
import uuid
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.user import User
from app.schemas.user_schema import UserUpdate
from app.utils.security import hash_password

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# 常量配置
# ──────────────────────────────────────────────

STATIC_DIR = Path("static")
AVATAR_DIR = STATIC_DIR / "avatars"
ALLOWED_AVATAR_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_AVATAR_SIZE: int = 5 * 1024 * 1024  # 5 MB

# 允许通过 update_user 修改的字段白名单
_USER_UPDATABLE_FIELDS: frozenset[str] = frozenset(
    {"username", "email", "is_active", "is_superuser"}
)

# 模块公开接口
__all__ = [
    "save_user_avatar",
    "get_user_avatar_url",
    "create_user",
    "get_user_by_username",
    "get_user_by_email",
    "get_user_by_id",
    "get_users",
    "update_user",
    "update_password",
    "deactivate_user",
]


# ──────────────────────────────────────────────
# 内部工具函数
# ──────────────────────────────────────────────

def _sanitize_filename(name: str) -> str:
    """将任意字符串清理为安全的文件名片段。

    只保留字母、数字、点、下划线、连字符；
    若清理后为空则回退为 ``"user"``。
    """
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "_", name).strip("._")
    return slug or "user"


def _build_avatar_path(user_id: int, username: str, ext: str) -> Path:
    """生成头像存储路径：``{user_id}_{safe_name}_{uuid8}{ext}``

    设计要点：
    - 以 ``user_id`` 开头 → 用户改名不影响已有文件检索
    - 加入 ``uuid`` 后缀 → 防止并发上传时文件名碰撞
    - 清理 ``username`` → 杜绝路径穿越（``../``）
    """
    unique = uuid.uuid4().hex[:8]
    safe_name = _sanitize_filename(username)
    return AVATAR_DIR / f"{user_id}_{safe_name}_{unique}{ext}"


def _remove_old_avatars(user_id: int) -> None:
    """删除指定用户的全部旧头像文件（按 user_id 前缀匹配）。
        Args:
                user_id: 已持久化的用户主键，**调用方必须保证非 None**。
    """
    if user_id is None:
        raise ValueError("无法删除旧头像：用户尚未持久化（id 为 None），请先创建用户")
    for old_file in AVATAR_DIR.glob(f"{user_id}_*"):
        try:
            old_file.unlink(missing_ok=True)
        except OSError:
            logger.warning("无法删除旧头像文件: %s", old_file, exc_info=True)


# ──────────────────────────────────────────────
# 头像服务
# ──────────────────────────────────────────────

async def save_user_avatar(
    user: User,
    file_data: bytes,
    original_filename: str,
) -> str:
    """保存用户头像到 ``static/avatars/``，返回可访问的 URL 路径。

    Args:
        user: 当前用户 ORM 对象（需已持久化，拥有 ``id``）。
        file_data: 上传文件的原始字节流。
        original_filename: 上传时的原始文件名（用于提取扩展名）。

    Returns:
        形如 ``/static/avatars/1_alice_a3f2c1d8.png`` 的相对 URL。

    Raises:
        ValueError: 文件超过大小限制，或者用户未持久化(id=None)时抛出。

    Note:
        此函数 **只操作文件系统**，不写数据库。
        若 ``User`` 模型有 ``avatar_url`` 字段，请在路由层调用后自行更新。
    """
    if user.id is None:
        raise ValueError("无法保存头像：用户尚未持久化（id 为 None），请先创建用户")
    # ① 大小校验 —— 防止磁盘耗尽型 DoS
    if len(file_data) > MAX_AVATAR_SIZE:
        max_mb = MAX_AVATAR_SIZE / (1024 * 1024)
        raise ValueError(f"头像文件过大，最大允许 {max_mb:.0f} MB")

    # ② 确保目录存在
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)

    # ③ 提取并校验扩展名，不合法则回退 .png
    ext = Path(original_filename).suffix.lower()
    if ext not in ALLOWED_AVATAR_EXTENSIONS:
        logger.info("不支持的头像扩展名 '%s'，回退为 .png", ext)
        ext = ".png"

    # ④ 清理旧头像 → 写入新文件
    _remove_old_avatars(user.id)
    avatar_path = _build_avatar_path(user.id, user.username, ext)
    avatar_path.write_bytes(file_data)

    logger.info("头像已保存: user_id=%s → %s", user.id, avatar_path.name)
    return f"/static/avatars/{avatar_path.name}"


def get_user_avatar_url(user: User) -> str | None:
    """根据用户对象查找已存在的头像文件，返回 URL 或 ``None``。"""
    if user is None or user.id is None:
        return None

    for ext in sorted(ALLOWED_AVATAR_EXTENSIONS):
        for candidate in AVATAR_DIR.glob(f"{user.id}_*{ext}"):
            return f"/static/avatars/{candidate.name}"
    return None


# ──────────────────────────────────────────────
# 用户 CRUD
# ──────────────────────────────────────────────

async def create_user(
    session: AsyncSession,
    username: str,
    email: str,
    password: str,
) -> User:
    """创建新用户。

    依赖数据库 **唯一约束** 防重复，冲突时抛 ``ValueError``。
    邮箱统一转小写存储；用户名保留原始大小写。
    """
    # 规范化输入（提前处理，便于日志 / 校验复用）
    username = username.strip()
    email = email.strip().lower()

    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
    )
    session.add(user)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        logger.warning("创建用户冲突: username=%s, email=%s", username, email)
        raise ValueError("用户名或邮箱已存在") from exc

    await session.refresh(user)
    logger.info("用户创建成功: id=%s, username=%s", user.id, user.username)
    return user


async def get_user_by_username(
    session: AsyncSession,
    username: str,
) -> User | None:
    """通过用户名查找用户（大小写不敏感）。

    使用 ``func.lower()`` 包裹输入值，使数据库有机会命中
    表达式索引（如 PostgreSQL ``citext`` / ``lower()`` 函数索引）。
    """
    result = await session.execute(
        select(User).where(
            func.lower(User.username) == func.lower(username.strip())
        )
    )
    return result.scalar_one_or_none()


async def get_user_by_email(
    session: AsyncSession,
    email: str,
) -> User | None:
    """通过邮箱查找用户（大小写不敏感）。

    存储时邮箱已统一小写，此处 ``func.lower`` 保持查询语义一致；
    若数据库已有 ``citext`` 或函数索引可自动命中。
    """
    result = await session.execute(
        select(User).where(
            func.lower(User.email) == email.strip().lower()
        )
    )
    return result.scalar_one_or_none()


async def get_user_by_id(
    session: AsyncSession,
    user_id: int,
) -> User | None:
    """通过主键查找用户。

    ``session.get()`` 是 SQLAlchemy 2.0 提供的主键快捷查询，
    优先走 Identity Map 缓存，比手动 ``select + where`` 更高效。
    """
    return await session.get(User, user_id)


async def get_users(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 20,
) -> list[User]:
    """分页获取用户列表。

    Args:
        skip: 跳过的记录数（偏移量）。
        limit: 每页最大返回条数，默认 20。
    """
    result = await session.execute(
        select(User).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def update_user(
    session: AsyncSession,
    user: User,
    data: UserUpdate,
) -> User:
    """更新用户信息。

    仅修改 ``_USER_UPDATABLE_FIELDS`` 白名单内的字段，
    防止通过 Schema 注入 ``hashed_password`` 等敏感字段。
    """
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field not in _USER_UPDATABLE_FIELDS:
            logger.debug("忽略非白名单字段: %s", field)
            continue
        setattr(user, field, value)

    await session.commit()
    await session.refresh(user)
    logger.info("用户信息已更新: user_id=%s", user.id)
    return user


async def update_password(
    session: AsyncSession,
    user: User,
    hashed_password: str,
) -> None:
    """更新用户密码。

    独立于 ``update_user``，确保密码字段不会出现在通用更新接口中。
    调用方应传入 **已哈希** 的密码，而非明文。
    """
    user.hashed_password = hashed_password
    await session.commit()
    logger.info("用户密码已更新: user_id=%s", user.id)


async def deactivate_user(
    session: AsyncSession,
    user: User,
) -> None:
    """软删除：禁用用户账户（``is_active = False``）。"""
    user.is_active = False
    await session.commit()
    logger.info("用户已禁用: user_id=%s, username=%s", user.id, user.username)
