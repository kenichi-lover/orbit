import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from secure import Secure, ContentSecurityPolicy
from secure.middleware import SecureASGIMiddleware
from slowapi.errors import RateLimitExceeded
from sqlmodel import SQLModel

from app.config.database import engine
from  app.config.settings import settings

from app.routers.api.auth import (
    router as auth_router
)

from app.routers.api.image import (
    router as image_router
)

from app.routers.api.user import (
    router as user_router
)

from app.routers.health import (
    router as health_router
) 

from app.routers.pages.index import (
    router as index_router
)

from app.routers.pages.story import (
    router as story_router
)
from app.routers.pages.photo import (
    router as photo_router
)
from app.routers.pages.profile import (
    router as profile_router
)
from app.config.database import async_session_factory
from app.dependencies.auth import resolve_user_from_cookie
from app.utils import limiter

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

@app.middleware("http")
async def user_cookie_middleware(request: Request, call_next):
    async with async_session_factory() as session:
        request.state.user = await resolve_user_from_cookie(request, session)
    return await call_next(request)

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
# 1. 构建 CSP 策略（推荐链式调用）
csp = (
    ContentSecurityPolicy()
    .default_src("'self'")  # 默认源：仅允许同源
    .script_src("'self'", "'unsafe-inline'")  # 脚本源：允许同源和内联脚本
    .script_src_attr("'self'", "'unsafe-inline'")  # 脚本属性源：允许同源和内联属性
)

# 2.直接在构造函数中传入 csp，同时保留默认头
secure_headers = Secure(
    csp=csp,
).with_default_headers()
app.add_middleware(SecureASGIMiddleware, secure=secure_headers)

app.include_router(auth_router, prefix="/api")
app.include_router(image_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(index_router)
app.include_router(story_router)
app.include_router(photo_router)
app.include_router(profile_router)
app.include_router(health_router)

app.mount("/static", StaticFiles(directory="static"), name="static")