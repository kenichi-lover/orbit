from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.dependencies.auth import resolve_user_from_cookie
from app.models.user import User
from app.services.user_service import get_user_avatar_url

from app.schemas.user_schema import UserPublic

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="templates")


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    user: Annotated[User | None, Depends(resolve_user_from_cookie)] = None,
):
    if not user:
        return RedirectResponse(url="/", status_code=302)

    profile_user = UserPublic.model_validate(user).model_dump(mode="json") if user else None
    if profile_user is not None:
        profile_user["avatar_url"] = get_user_avatar_url(user)

    return templates.TemplateResponse(
        request,
        "pages/profile.html",
        {
            "request": request,
            "title": "个人中心 - Orbit Gallery",
            "active_page": "profile",
            "user": profile_user,
        },
    )