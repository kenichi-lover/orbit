from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ImageBaseSchema(BaseModel):
    """Base schema for image metadata shared across create/read/update flows."""

    title: str | None = Field(default=None, max_length=100, description="Title of the image")
    description: str | None = Field(default=None, max_length=500, description="Description of the image")
    alt_text: str | None = Field(default=None, max_length=255, description="Alt text for accessibility")


class ImageCreateSchema(ImageBaseSchema):
    """Schema for creating a new image."""

    original_filename: str = Field(..., min_length=1, max_length=255, description="Original filename of the image")
    file_name: str = Field(..., min_length=1, max_length=255, description="Stored filename")
    relative_path: str = Field(..., min_length=1, max_length=500, description="Storage path of the image")
    thumbnail_relative_path: str | None = Field(default=None, min_length=1, max_length=500, description="Thumbnail path of the image")
    file_size: int = Field(default=0, ge=0, description="File size in bytes")
    mime_type: str = Field(default="image/jpeg", max_length=100, description="Image MIME type")
    width: int | None = Field(default=None, ge=0)
    height: int | None = Field(default=None, ge=0)
    user_id: int


class ImageReadSchema(ImageBaseSchema):
    """Schema for reading an image."""

    id: int
    original_filename: str
    file_name: str
    relative_path: str
    thumbnail_relative_path: str | None
    file_size: int
    mime_type: str
    width: int | None
    height: int | None
    created_at: datetime
    updated_at: datetime | None
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class ImagePublic(ImageReadSchema):
    """Public-facing image payload used in API responses."""
    author_name: str | None = Field(default=None, description="Username of the image author")

class ImageUpdateSchema(BaseModel):
    """Schema for updating an image."""

    title: str | None = Field(default=None, max_length=100, description="Title of the image")
    description: str | None = Field(default=None, max_length=500, description="Description of the image")
    alt_text: str | None = Field(default=None, max_length=255, description="Alt text for accessibility")
