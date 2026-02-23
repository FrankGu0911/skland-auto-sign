"""FastAPI Web 应用

提供 Web 管理界面和 API 接口。
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse

from database import db
from config import config, get_data_dir
from utils.logger import logger
from scheduler import job_manager
from api.routes import accounts, sign, records, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("Web API 启动中...")
    await db.init()
    job_manager.start()
    yield
    # 关闭时
    logger.info("Web API 关闭中...")
    job_manager.shutdown()
    await db.close()


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title=config.app.name,
        version=config.app.version,
        description="森空岛自动签到系统",
        lifespan=lifespan,
    )

    # 静态文件目录
    static_dir = Path(__file__).parent.parent / "api" / "static"
    static_dir.mkdir(parents=True, exist_ok=True)

    # 挂载静态文件
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # 模板目录
    templates_dir = Path(__file__).parent / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)
    templates = Jinja2Templates(directory=str(templates_dir))

    # 注册路由
    app.include_router(accounts.router, prefix="/api/accounts", tags=["账号管理"])
    app.include_router(sign.router, prefix="/api/sign", tags=["签到管理"])
    app.include_router(records.router, prefix="/api/records", tags=["签到记录"])
    app.include_router(stats.router, prefix="/api/stats", tags=["统计信息"])

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        """首页"""
        return templates.TemplateResponse("index.html", {"request": request})

    @app.get("/health")
    async def health():
        """健康检查"""
        return {"status": "ok", "version": config.app.version}

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """全局异常处理"""
        logger.error(f"API 错误: {exc}")
        return JSONResponse(
            status_code=500,
            content={"error": str(exc)}
        )

    return app


# 创建应用实例
app = create_app()
