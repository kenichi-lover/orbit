from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.user import User
from app.utils.security import hash_password


async def create_user(
    session: AsyncSession,
    username: str,
    email: str,
    password: str,
) -> User:
    """创建新用户。依赖数据库唯一约束防重复，冲突时抛 ValueError。"""
    # 规范化：邮箱统一小写，用户名保持原样（或按项目需求处理）
    email = email.strip().lower()
    username = username.strip()
    
    hashed_password = hash_password(password)
    
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
    )
    session.add(user)
    
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        # 判断是哪个字段冲突（PostgreSQL 可以通过 exc.orig.diag.constraint_name 精确判断）
        raise ValueError("Username or email already exists") from exc
    
    await session.refresh(user)
    return user


async def get_user_by_username(
    session: AsyncSession,
    username: str,
) -> User | None:
    """通过用户名查找用户（不区分大小写）。"""
    result = await session.execute(
        select(User).where(User.username.ilike(username.strip()))
    )
    return result.scalar_one_or_none()


async def get_user_by_email(
    session: AsyncSession,
    email: str,
) -> User | None:
    """通过邮箱查找用户（不区分大小写）。"""
    result = await session.execute(
        select(User).where(User.email.ilike(email.strip().lower()))
    )
    return result.scalar_one_or_none()


async def get_user_by_id(
    session: AsyncSession,
    user_id: int,
) -> User | None:
    """通过 ID 查找用户。"""
    return await session.get(User, user_id)