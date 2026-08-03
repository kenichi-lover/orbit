from datetime import datetime
from typing import TYPE_CHECKING
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func

if TYPE_CHECKING:
    from app.models.image import Image  # 避免循环导入问题
    
class User(SQLModel, table=True):
    __tablename__: str = "users"

    id: int | None = Field(default=None, primary_key=True)

    username: str = Field(index=True, unique=True, max_length=50)
    email: str = Field(index=True, unique=True, max_length=100)

    hashed_password: str = Field(max_length=255)

    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    
    created_at: datetime | None = Field(
        default=None,    # <--- 新增：允许 Python 不传值
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),     # 数据库会自动填充
            onupdate=func.now(),
            index=True
        )
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True), 
            server_default=func.now(),
            onupdate=func.now(),
        )
    )

    def to_dict(self) -> dict:
        """将 User 对象转换为字典，排除敏感信息"""
        return {
            "id": self.id,
            "username": self.username,
        }


    images: list["Image"] = Relationship(back_populates="author")