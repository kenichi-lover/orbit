from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config.database import get_session
from app.services import image_service

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="templates")

@router.get("/photo/{photo_id}", response_class=HTMLResponse)
async def photo_detail(request: Request, photo_id: int):
    user = getattr(request.state, "user", None)
    async for session in get_session():
       image = await image_service.get_image_by_id(session, photo_id)
       break
    if not image or image.is_deleted:
           raise HTTPException(status_code=404, detail="Photo not found")
    return templates.TemplateResponse(
         request,
         "pages/photo_detail.html", 
        {
            "request": request,
            "title": f"{image.title or '未知图片'} - Orbit Gallery",
            "active_page": "explore",  # 或 "photo"
            "user": user,
            "photo": image,
        }
    )
