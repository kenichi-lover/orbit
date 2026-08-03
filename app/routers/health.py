import logging
from fastapi import APIRouter, HTTPException
from sqlmodel import text
from app.config.database import engine

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def health_check():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Service Unavailable")


