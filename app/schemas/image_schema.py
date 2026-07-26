from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ImageBaseSchema(BaseModel):
    """Base schema for image metadata shared across create/read/update flows."""

    title: str | None = Field(default=None, max_length=100, description="Title of the image")
    description: str | None = Field(default=None, max_length=500, description="Description of the image")
    alt_text: str | None = Field(default=None, max_length=255, description="Alt text for accessibility")
    category: str = Field(default="Gallery", max_length=100, description="Image category/album")
    tags: str | None = Field(default=None, max_length=500, description="Comma-separated tags")


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
    user_name: str = Field(..., description="Username of the uploader")


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
    user_name: str

    model_config = ConfigDict(from_attributes=True)


class ImagePublic(BaseModel):
    """Public-facing image payload used in API responses."""

    id: int
    url: str = Field(..., description="Full URL to access the image")
    title: str
    category: str
    description: str | None
    tags: str | None
    author_name: str | None = Field(default=None, description="Username of the image author")

class ImageUpdateSchema(BaseModel):
    """Schema for updating an image."""

    title: str | None = Field(default=None, max_length=100, description="Title of the image")
    description: str | None = Field(default=None, max_length=500, description="Description of the image")
    alt_text: str | None = Field(default=None, max_length=255, description="Alt text for accessibility")
    category: str | None = Field(default=None, max_length=100, description="Image category/album")
    tags: str | None = Field(default=None, max_length=500, description="Comma-separated tags")


class ImageSearchParams(BaseModel):
    """Query parameters for searching images."""

    q: str | None = Field(default=None, max_length=200, description="Keyword to search in title/description")
    category: str | None = Field(default=None, max_length=100, description="Filter by category")
    tag: str | None = Field(default=None, max_length=100, description="Filter by tag (exact match)")
    user_name: str | None = Field(default=None, max_length=50, description="Filter by author username")
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
