from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.schemas.user_schema import UserPublic

router = APIRouter(tags=["pages"])

templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = getattr(request.state, "user", None)
    return templates.TemplateResponse(
        request,
        "pages/index.html",
        {
            "request": request, # 注意：context 里仍需保留 request 键，供 Jinja2 使用
            "title": "Orbit Gallery",
            "active_page": "explore",
            # ✅ 用 UserPublic 白名单过滤 + mode="json" 确保 datetime → ISO 字符串
            "user": UserPublic.model_validate(user). model_dump(mode="json") if user else None,
        }
    )

