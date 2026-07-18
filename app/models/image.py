from datetime import datetime

from sqlmodel import DATETIME, Column, Field, Relationship, SQLModel, func

from app.models.user import User


class Image(SQLModel, table=True):
    __tablename__ = "images"

    id: int | None = Field(default=None, primary_key=True)

    filename: str = Field(
        index=True, 
        unique=True, 
        max_length=255)   # 原始文件名
    storage_path: str = Field(
        index=True, 
        unique=True, 
        max_length=500)    # 存储路径，指向实际存储的文件位置
    thumbnail_path: str | None = Field(
        default=None, 
        index=True, 
        unique=True, 
        max_length=500)   # 缩略图路径，指向缩略图的存储位置
    
    title: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)

    created_at: datetime = Field(
        sa_column=Column(
            DATETIME(timezone=True), 
            server_default=func.now(),
            index=True
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DATETIME(timezone=True), 
            server_default=func.now(),
            onupdate=func.now(),
            index=True
        )
    )


user_id: int = Field(
    foreign_key="users.id",
    index=True,
    nullable=False
)
author: "User" = Relationship(back_populates="images")