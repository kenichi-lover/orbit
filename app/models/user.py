from typing import TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy.orm import Mapped
from app.models.mixins import TimestampMixin
from app.schemas.user_schema import UserPublic

if TYPE_CHECKING:
    from app.models.image import Image  # 避免循环导入问题
    
class User(TimestampMixin, SQLModel, table=True):
    __tablename__: str = "users"

    id: int | None = Field(default=None, primary_key=True)

    username: str = Field(index=True, unique=True, max_length=50)
    email: str = Field(index=True, unique=True, max_length=100)

    # 排除敏感信息，避免在序列化时泄露
    # exclude=True → model_dump() 序列化时自动跳过该字段
    hashed_password: str = Field(max_length=255, exclude=True)  

    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    

    def to_public(self) -> UserPublic:
        """显式转换，比 to_dict 类型安全"""
        return UserPublic.model_validate(self)


    images: Mapped[list["Image"]] = Relationship(back_populates="author")