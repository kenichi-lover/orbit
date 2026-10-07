import logging
#from logging.handlers import RotatingFileHandler
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from sqlmodel import SQLModel

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from secure import Secure, ContentSecurityPolicy
from secure.middleware import SecureASGIMiddleware
from slowapi.errors import RateLimitExceeded

from app.config.database import async_session_factory, engine
from app.config.settings import settings
from app.dependencies.auth import resolve_user_from_cookie
from app.routers.api.auth import router as auth_router
from app.routers.api.image import router as image_router
from app.routers.api.user import router as user_router
from app.routers.api.user_admin import router as admin_user_router
from app.routers.health import router as health_router
from app.routers.pages.index import router as index_router
from app.routers.pages.story import router as story_router
from app.routers.pages.photo import router as photo_router
from app.routers.pages.profile import router as profile_router
from app.utils import limiter

# ============================================================
# P1-4: 结构化日志配置（structlog）
# ============================================================
# 进程启动前先确保 logs 目录存在，否则 RotatingFileHandler 会报错
#Path("logs").mkdir(parents=True, exist_ok=True)

# ----------1. 公共处理器：两种格式共享的部分 ----------
structlog_processors = [
        structlog.contextvars.merge_contextvars,   # 合并请求级上下文(request_id等)
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
# ---------- 2.按环境选择最终渲染器 ----------
if settings.LOG_FORMAT == "json":
    # 生产：机器可读的 JSON，供日志收集器(Prometheus/Loki/ELK)解析
    final_renderer = structlog.processors.JSONRenderer()
else:
    from structlog.dev import ConsoleRenderer
    final_renderer = ConsoleRenderer(colors=True)
# ---------- ③ 然后配置 structlog ----------
structlog.configure(
    processors=[*structlog_processors, final_renderer],
    wrapper_class=structlog.make_filtering_bound_logger(
        logging.DEBUG if settings.DEBUG else logging.INFO
    ),
    logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
    cache_logger_on_first_use=True,
)
# ---------- ④ 最后挂文件 handler（仅生产） ----------
#if settings.LOG_FORMAT == "json":
#    from logging.handlers import RotatingFileHandler
#    file_handler = RotatingFileHandler(
#        "logs/app.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
#    )
#    file_handler.setFormatter(logging.Formatter("%(message)s"))
#    logging.getLogger().addHandler(file_handler)
#
logger = structlog.get_logger(__name__)


# ============================================================
# P0-2: 需要在启动时确保存在的运行时目录
# ============================================================
REQUIRED_DIRS = [
    Path("uploads"),
    Path("static/images"),
    Path("static/avatars"),
#    Path("logs"),
]


# ============================================================
# Lifespan：只做资源初始化与释放，不做任何 DDL
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "startup_begin",
        app_env=settings.APP_ENV,
        debug=settings.DEBUG,
    )

    # P0-2: 自动创建运行时目录
    for d in REQUIRED_DIRS:
        d.mkdir(parents=True, exist_ok=True)
    logger.info("runtime_dirs_ready", dirs=[str(d) for d in REQUIRED_DIRS])

    # P0-4: 数据库 schema 不再由应用启动时创建
    # 所有表结构统一走 Alembic：alembic upgrade head
    # 开发环境首此初始化请运行：alembic upgrade head
    if settings.APP_ENV == "development":
        logger.warning(
            "app_env_is_development",
            hint="请确认 .env 中 APP_ENV 是否正确；生产部署必须为 production",
        )
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
    else:
        logger.info("prod env: schema managed by alembic")

    yield

    logger.info("shutdown_begin")
    await engine.dispose()
    logger.info("shutdown_complete")


app = FastAPI(
    title="Orbit Gallery",
    lifespan=lifespan,
)


# ============================================================
# P1-4: Request ID 中间件
# 注意：FastAPI 中 @app.middleware 后定义的中间件位于最外层
#       因此此中间件必须放在 user_cookie_middleware 之后定义
# ============================================================
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    structlog.contextvars.clear_contextvars()
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:16]
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        path=request.url.path,
        method=request.method,
    )
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ============================================================
# 用户 Cookie 解析中间件
# 优化：静态资源与 /health 路径直接放行，避免无谓的 DB 会话开销
# ============================================================
EXCLUDED_PATH_PREFIXES = ("/static", "/favicon.ico", "/health")

@app.middleware("http")
async def user_cookie_middleware(request: Request, call_next):
    if any(request.url.path.startswith(p) for p in EXCLUDED_PATH_PREFIXES):
        request.state.user = None
        return await call_next(request)

    async with async_session_factory() as session:
        user = await resolve_user_from_cookie(request, session)
        request.state.user = (
            user.to_public().model_dump(mode="json") if user else None
        )
    return await call_next(request)


# ============================================================
# 限流器 + 异常处理
# ============================================================
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)  # type: ignore
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded. Please try again later.{exc.detail}"},
    )


# ============================================================
# 安全响应头中间件
# ============================================================
csp = (
    ContentSecurityPolicy()
    .default_src("'self'")
    .script_src("'self'", "'unsafe-inline'")
    .script_src_attr("'self'", "'unsafe-inline'")
    .img_src("'self'", "data:", "https://images.unsplash.com", "https://cdn.jsdelivr.net")
    .font_src("'self'", "https://fonts.gstatic.com")
    .connect_src("'self'")
)

secure_headers = Secure(csp=csp).with_default_headers()
app.add_middleware(SecureASGIMiddleware, secure=secure_headers)


# ============================================================
# 路由注册
# ============================================================
app.include_router(auth_router, prefix="/api")
app.include_router(image_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(admin_user_router, prefix="/api")
app.include_router(index_router)
app.include_router(story_router)
app.include_router(photo_router)
app.include_router(profile_router)
app.include_router(health_router)

app.mount("/static", StaticFiles(directory="static"), name="static")

