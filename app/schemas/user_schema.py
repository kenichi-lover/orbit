from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserbaseSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email:  EmailStr 

class UserCreateSchema(UserbaseSchema):
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=100)

class UserReadSchema(UserbaseSchema):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserUpdateSchema(UserbaseSchema):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None
    is_superuser: bool | None = None

class UserLoginSchema(UserbaseSchema):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str | None = None

