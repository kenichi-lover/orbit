from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ARRAY, Column, String
from sqlmodel import Field, Relationship, SQLModel

from app.models.mixins import TimestampMixin
from app.utils.enums import Category

if TYPE_CHECKING:
    from app.models.user import User


# ══════════════════════════════════════════════
# 模块 5: Schema 分层 — Base（用户可编辑字段）
# ══════════════════════════════════════════════

class ImageBase(SQLModel):
    """用户可控的业务字段。

    继承者：ImageCreate / ImageUpdate / ImagePublic
    ⚠️ 不包含 file_name / relative_path 等内部存储字段
    """

    title: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    alt_text: str | None = Field(default=None, max_length=255)

    # ── 模块 3: category 绑定枚举 ──
    category: Category = Field(default=Category.GALLERY)

    # ✅ 修复：tags 在 Base 层只做 Pydantic 验证
    # 实际列定义放在 Image 表模型中用 sa_column
    tags: list[str] = Field(default_factory=list)



# ══════════════════════════════════════════════
# 模块 1-4: 数据库表模型
# ══════════════════════════════════════════════

class Image(ImageBase, TimestampMixin, SQLModel, table=True):
    """images 表"""

    __tablename__: str = "images"

    id: int | None = Field(default=None, primary_key=True)

    # ── 存储定位 ──
    original_filename: str = Field(max_length=255)
    file_name: str = Field(index=True, unique=True, max_length=255)
    relative_path: str = Field(max_length=500)
    thumbnail_relative_path: str | None = Field(default=None, max_length=500)

    # ── 模块 4: 文件元数据（服务端计算）──
    file_size: int = Field(default=0, ge=0)
    mime_type: str = Field(default="image/webp", max_length=100)  # ✅ 修正 typo
    width: int | None = Field(default=None, ge=0)
    height: int | None = Field(default=None, ge=0)

    # ✅ 修复：tags 的实际列定义
    # sa_column 完全跳过 SQLModel 的自动类型推导
    # Pydantic 验证仍由 ImageBase.tags: list[str] 提供
    tags: list[str] = Field(
        default_factory=list,
        sa_column=Column(
            ARRAY(String),
            nullable=False,
            server_default="{}",      # PostgreSQL 空数组语法
        ),
    )


    # ── 模块 3: category 列约束 ──
    # SQLModel 自动将 str Enum 映射为 VARCHAR + CHECK
    # 如需原生 PG ENUM 可加 sa_column=Column(pg_enum(Category))

    # ── 软删除 ──
    is_deleted: bool = Field(default=False, index=True)
    deleted_at: datetime | None = Field(default=None)

    # ── 模块 1: 外键改为 author_id (int) ──
    author_id: int = Field(foreign_key="users.id", index=True, nullable=False)
    author: "User" = Relationship(back_populates="images")


