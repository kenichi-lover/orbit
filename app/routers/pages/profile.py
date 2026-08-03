from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="templates")

@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    user = getattr(request.state, "user", None)
    # 未登录重定向到首页（或弹出登录框）
    if not user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(
        request,
        "pages/profile.html", 
        {
            "request": request,
            "title": "个人中心 - Orbit Gallery",
            "active_page": "profile",
            "user": user,
        }
    )