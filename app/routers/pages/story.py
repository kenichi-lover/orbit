from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="templates")

@router.get("/story", response_class=HTMLResponse)
async def story_page(request: Request):
    user = getattr(request.state, "user", None)

    # ✅ 直接序列化，hashed_password 已被模型自动排除
    user_data = (
        user.model_dump(
            mode="json",
            exclude={"hashed_password", "email", "is_active", "is_superuser", "created_at", "updated_at"}
        ) 
        if user is not None 
        else None
    )

    return templates.TemplateResponse(
        request,
        "pages/story.html",
        {
            "request": request,
            "title": "叙事 - Orbit Gallery",
            "active_page": "story",
            "user": user_data,               # ✅ 传入字典而非原始对象
        },
    )