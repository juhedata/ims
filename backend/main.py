from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.core.config import settings
from app.core.logger import setup_logger
from app.api.router import api_router


def run_migrations_if_enabled() -> None:
    """
    根据 AUTO_MIGRATE 配置决定是否自动执行数据库迁移。
    生产环境建议关闭，由部署流程手动执行 alembic upgrade head。
    使用 subprocess 调用，避免跨 Python 版本的 import 冲突。
    """
    if not settings.AUTO_MIGRATE:
        logger.info("AUTO_MIGRATE=false，跳过自动数据库迁移")
        return

    import subprocess
    import sys

    try:
        logger.info("开始执行数据库迁移（alembic upgrade head）...")
        # 使用当前进程的 Python 解释器调用 alembic，确保与虚拟环境一致
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        logger.info("数据库迁移完成")
    except Exception as e:
        logger.error(f"数据库迁移失败：{e}")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动前初始化，关闭时清理。"""
    # ── 启动阶段 ──────────────────────────────────────────────────
    setup_logger(settings.LOG_LEVEL)
    logger.info(f"启动 {settings.APP_NAME}，DEBUG={settings.DEBUG}")

    # 检查数据库连接
    from app.db.database import check_db_connection
    if check_db_connection():
        logger.info("数据库连接正常")
    else:
        logger.error("数据库连接失败，请检查配置！")

    # 按需执行迁移
    run_migrations_if_enabled()

    # 启动定时任务（日库存快照）
    from app.core.scheduler import start_scheduler, stop_scheduler
    start_scheduler()

    yield

    # ── 关闭阶段 ──────────────────────────────────────────────────
    stop_scheduler()
    logger.info(f"{settings.APP_NAME} 已关闭")


def create_app() -> FastAPI:
    """工厂函数：创建并配置 FastAPI 实例。"""
    app = FastAPI(
        title=settings.APP_NAME,
        description="IMS — 一物一码库存管理系统 API",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,       # 生产环境隐藏 Swagger
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # ── CORS 跨域 ────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── 全局异常处理 ──────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """捕获未处理的异常，返回统一错误格式并记录日志。"""
        logger.exception(f"未处理异常 [{request.method} {request.url}]: {exc}")
        return JSONResponse(
            status_code=500,
            content={"code": 500, "msg": "服务器内部错误", "data": None},
        )

    # ── 挂载路由 ─────────────────────────────────────────────────
    app.include_router(api_router)

    # ── 静态上传目录（Logo 等）───────────────────────────────────
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.mount(
        settings.UPLOAD_URL_PREFIX,
        StaticFiles(directory=str(upload_dir)),
        name="uploads",
    )

    # ── 健康检查（不需要鉴权）────────────────────────────────────
    @app.get("/health", tags=["系统"], summary="健康检查")
    def health_check():
        """用于 K8s / 负载均衡器探活，始终返回 200。"""
        return {"status": "ok", "app": settings.APP_NAME}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
    )
