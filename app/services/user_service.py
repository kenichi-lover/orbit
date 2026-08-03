from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.user import User
from app.schemas.user_schema import UserUpdateSchema
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

# 使用 func.lower 进行精确比较
async def get_user_by_username(
    session: AsyncSession,
    username: str,
) -> User | None:
    """将数据库字段和输入值都转为小写进行比较"""
    result = await session.execute(
        select(User).where(
            func.lower(User.username) == func.lower(
                username.strip()
            )
        )
    )
    return result.scalar_one_or_none()


async def get_user_by_email(
    session: AsyncSession,
    email: str,
) -> User | None:
    """
    通过邮箱查找用户,
    利用已知的存储格式（全小写），直接精确匹配
    """
    result = await session.execute(
        select(User).where(
            func.lower(User.email) == email.strip().lower()
        )
    )
    return result.scalar_one_or_none()

"""
session.get(User, user_id) 是 SQLAlchemy 2.0 / SQLModel 专门提供的快捷方法，
专门用于通过**主键（Primary Key）**查找对象。
它内部封装了 select 和 where 的逻辑，一行代码搞定，可读性更高。
"""
async def get_user_by_id(
    session: AsyncSession,
    user_id: int,
) -> User | None:
    """通过 ID 查找用户。"""
    return await session.get(User, user_id)


async def get_users(
        session: AsyncSession,
        skip: int = 0,
        limit: int = 10
) -> list[User]:
    result = await session.execute(
        select(User).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def update_user(session: AsyncSession, user: User, data: UserUpdateSchema) -> User:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    await session.commit()
    await session.refresh(user)
    return user


async def update_password(session: AsyncSession, user: User, hashed_password: str) -> None:
    user.hashed_password = hashed_password
    await session.commit()


async def deactivate_user(session: AsyncSession, user: User) -> None:
    user.is_active = False
    await session.commit()