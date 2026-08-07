from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.dependencies.auth import resolve_user_from_cookie
from app.models.user import User

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="templates")


@router.get("/story", response_class=HTMLResponse)
async def story_page(
    request: Request,
    current_user: Annotated[User | None, Depends(resolve_user_from_cookie)] = None,
):
    # 说明：故事页的当前用户必须从登录 cookie 解析，而不是依赖 request.state.user。
    # 这样即使页面路由没有显式挂载中间件，前端依然能拿到正确的登录信息。
    user_data = None
    if current_user is not None:
        user_data = current_user.model_dump(
            mode="json",
            exclude={"hashed_password", "email", "is_active", "created_at", "updated_at"},
        )

    return templates.TemplateResponse(
        request,
        "pages/story.html",
        {
            "request": request,
            "title": "叙事 - Orbit Gallery",
            "active_page": "story",
            "user": user_data,  # 传入字典给模板和前端脚本使用
        },
    )