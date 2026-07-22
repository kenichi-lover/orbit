from datetime import datetime

from sqlmodel import DATETIME, Column, Field, Relationship, SQLModel, func

from app.models.user import User


class Image(SQLModel, table=True):
    __tablename__: str = "images"

    id: int | None = Field(default=None, primary_key=True)

    # 原始文件名（仅展示，不用于存储定位）
    original_filename: str = Field(max_length=255)

    # 实际存储用的唯一文件名
    file_name: str = Field(index=True, unique=True, max_length=255)
    
    # 相对路径（从 static/ 目录起算），便于迁移和换域名
    relative_path: str = Field(max_length=500)
    thumbnail_relative_path: str | None = Field(default=None, max_length=500)
    
    # 文件元数据
    file_size: int = Field(default=0)                     # 字节
    mime_type: str = Field(default="images/webp", max_length=100)
    width: int | None = Field(default=None)
    height: int | None = Field(default=None)

    # 业务信息
    title: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    alt_text: str | None = Field(default=None, max_length=255)  # 无障碍属性

    created_at: datetime = Field(
        default= None,
        sa_column=Column(
            DATETIME(timezone=True), 
            server_default=func.now(),
            index=True
        )
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            DATETIME(timezone=True), 
            onupdate=func.now()
        )
    )

    # 软删除
    is_deleted: bool = Field(default=False, index=True)
    deleted_at: datetime | None = Field(default=None)


    user_name: str = Field(
        foreign_key="users.username",
        index=True,
        nullable=False
    )
    author: "User" = Relationship(back_populates="images")