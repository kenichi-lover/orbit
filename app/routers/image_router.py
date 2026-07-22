from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_session
from app.models.user import User
from app.schemas.image_schema import ImagePublic
from app.services.image_service import get_images_by_user
from app.utils.pagination import PaginatedResponse, PaginationParams

router = APIRouter()


@router.get("/images", response_model=PaginatedResponse[ImagePublic])
async def list_images(
    p: Annotated[PaginationParams, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
    user_name: str | None = None,
) -> PaginatedResponse[ImagePublic]:
    items, total = await get_images_by_user(
        session,
        user_name=user_name,
        skip=p.skip,
        limit=p.limit,
    )
    return PaginatedResponse.create(
        items=items,
        total=total,
        skip=p.skip,
        limit=p.limit,
    )