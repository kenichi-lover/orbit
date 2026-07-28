import logging
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from secure import Secure
from secure.middleware import SecureASGIMiddleware
from slowapi.errors import RateLimitExceeded
from sqlmodel import SQLModel, text
from  app.config.settings import settings
from app.config.database import engine
from fastapi import FastAPI, HTTPException, Request

from app.routers.auth import (
    router as auth_router
)

from app.routers.image import (
    router as image_router
)

from app.routers.index import (
    router as index_router
)

from app.utils import limiter
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting up... {settings.APP_ENV}")

    if settings.APP_ENV == "development":
        logger.warning(
            "Development environment detected. Dropping and recreating the database..."
            )
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("Database created successfully.")
    else:
        logger.info(
            "Production environment detected. Skipping database creation."
            )

    yield

    logger.info("Shutting down...")

    await engine.dispose()

    logger.info("Shutdown complete.")



app = FastAPI(
    title="Orbit Gallery",
    lifespan=lifespan,
)

app.state.limiter = limiter
@app.exception_handler(RateLimitExceeded) # type: ignore
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded. Please try again later.{exc.detail}"},
    )

# 注册安全 HTTP 头中间件
"""
如果不使用中间件，需要在每个路由处理函数或每个响应中手动添加这些头。
这不仅代码冗余，而且容易在新增接口时忘记添加。
中间件实现了“一次配置，全局覆盖”。
"""
secure_headers = Secure.with_default_headers()
# 允许内联脚本和 script 属性（模板中使用 inline <script> + onclick）
for _h in secure_headers.headers_list:
    if "ContentSecurity" in type(_h).__name__:
        _h._directives["script-src"] = ["'self'", "'unsafe-inline'"]
        _h._directives["script-src-attr"] = ["'self'", "'unsafe-inline'"]
        break
app.add_middleware(SecureASGIMiddleware, secure=secure_headers)

app.include_router(auth_router)
app.include_router(image_router, prefix="/api")
app.include_router(index_router)

@app.get("/health")
async def health_check():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service Unavailable")

app.mount("/static", StaticFiles(directory="static"), name="static")