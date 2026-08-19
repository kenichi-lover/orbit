from datetime import datetime

from pydantic import EmailStr, Field
from sqlmodel import SQLModel


# ═══════════════════════════════════════════════════
# 基础字段
# ═══════════════════════════════════════════════════

class UserBase(SQLModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


# ═══════════════════════════════════════════════════
# 请求体（Request）
# ═══════════════════════════════════════════════════

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=100)


class UserUpdate(SQLModel):
    """全部字段可选，适合 PATCH 式更新"""
    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None
    is_superuser: bool | None = None


class UserPasswordUpdate(SQLModel):
    old_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)


class UserLogin(SQLModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)


# ═══════════════════════════════════════════════════
# 响应体（Response）
# ═══════════════════════════════════════════════════

class UserPublic(UserBase):
    """对外暴露的用户信息。可直接作为 response_model，替代 to_dict()。"""
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    # 允许从 ORM 对象（如 User）直接序列化
    model_config = {"from_attributes": True}


class TokenResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"


# ═══════════════════════════════════════════════════
# 导出
# ═══════════════════════════════════════════════════

__all__ = [
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserPasswordUpdate",
    "UserLogin",
    "UserPublic",
    "TokenResponse",
]
