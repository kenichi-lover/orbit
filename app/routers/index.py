"""页面渲染路由 — 返回 HTML（非 JSON API）。"""

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from app.config.database import get_session
from app.dependencies.auth import resolve_user_from_cookie

router = APIRouter()

_templates = Jinja2Templates(directory="templates")


@router.get("/")
async def index(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """首页：渲染轨道舞台，传入当前登录用户信息。"""
    user = None
    try:
        user = await resolve_user_from_cookie(request, session)
    except Exception:
        pass

    # 将 user 转为 dict 供模板使用
    user_data = None
    if user:
        user_data = {
            "id": user.id,
            "username": user.username,
        }

    return _templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "Orbit Gallery",
            "user": user_data,
        },
    )
