from datetime import datetime
from typing import TYPE_CHECKING
from sqlmodel import DATETIME, Column, Field, Relationship, SQLModel, func

if TYPE_CHECKING:
    from app.models.image import Image  # 避免循环导入问题
    
class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)

    username: str = Field(index=True, unique=True, max_length=50)
    email: str = Field(index=True, unique=True, max_length=100)

    hashed_password: str = Field(max_length=255)

    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    
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


images: list["Image"] = Relationship(back_populates="author")