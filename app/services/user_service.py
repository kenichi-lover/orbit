"""
用户服务层：仅负责用户实体的数据库 CRUD
"""

import logging
from typing import Any

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.user import User
from app.schemas.user_schema import UserUpdate
from app.utils.security import hash_password

logger = logging.getLogger(__name__)

# 允许通过 update_user 修改的字段白名单
_USER_UPDATABLE_FIELDS: frozenset[str] = frozenset(
    {"username", "email", "is_active", "is_superuser"}
)

__all__ = [
    "create_user",
    "get_user_by_username",
    "get_user_by_email",
    "get_user_by_id",
    "get_users",
    "update_user",
    "update_password",
    "deactivate_user",
    "update_avatar_url",  # 新增：专门用于更新头像 URL
]


# ──────────────────────────────────────────────
# 用户 CRUD
# ──────────────────────────────────────────────

async def create_user(
    session: AsyncSession,
    username: str,
    email: str,
    password: str,
) -> User:
    """创建新用户。"""
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
    """通过用户名查找用户（大小写不敏感）。"""
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
    """通过邮箱查找用户（大小写不敏感）。"""
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
    """通过主键查找用户。"""
    return await session.get(User, user_id)


async def get_users(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 20,
) -> list[User]:
    """分页获取用户列表。"""
    result = await session.execute(
        select(User).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def update_user(
    session: AsyncSession,
    user: User,
    data: UserUpdate,
) -> User:
    """更新用户基本信息。"""
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
    """更新用户密码。"""
    user.hashed_password = hashed_password
    await session.commit()
    logger.info("用户密码已更新: user_id=%s", user.id)


async def deactivate_user(
    session: AsyncSession,
    user: User,
) -> None:
    """软删除：禁用用户账户。"""
    user.is_active = False
    await session.commit()
    logger.info("用户已禁用: user_id=%s, username=%s", user.id, user.username)


async def update_avatar_url(
    session: AsyncSession,
    user: User,
    avatar_url: str,
) -> None:
    """更新用户的头像 URL 字段。
    
    此函数不处理文件存储，仅负责将 URL 持久化到数据库。
    文件存储逻辑应在路由层调用 StorageService 完成。
    """
    user.avatar_url = avatar_url
    await session.commit()
    logger.info("用户头像 URL 已更新: user_id=%s, url=%s", user.id, avatar_url)

