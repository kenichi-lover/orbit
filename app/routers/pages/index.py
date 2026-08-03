from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

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
            "user": user.to_dict() if user else None,  # 将 User 对象转换为字典，排除敏感信息
        }
    )

