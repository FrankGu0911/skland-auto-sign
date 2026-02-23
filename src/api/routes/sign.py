"""签到管理 API"""

from typing import Literal

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from database import db
from models import User
from core.sign_service import sign_user, sign_all_users
from utils.logger import logger

router = APIRouter()


class SignTaskResponse(BaseModel):
    """签到任务响应"""
    task_id: str
    message: str


class SignResult(BaseModel):
    """签到结果"""
    total: int
    success: int
    failed: int
    duplicate: int
    details: dict[str, str]


@router.post("/run")
async def run_sign(game: Literal["arknights", "endfield", "all"] = "all", background_tasks: BackgroundTasks = None):
    """执行签到

    Args:
        game: 游戏类型
        background_tasks: 后台任务

    Returns:
        签到结果
    """
    logger.info(f"收到签到请求，游戏类型: {game}")

    try:
        async with db.get_session() as session:
            results = await sign_all_users(session, game)

            # 转换结果格式
            formatted_results = {}
            for user_name, result in results.items():
                formatted_results[user_name] = {
                    "total": result.total,
                    "success": result.success,
                    "failed": result.failed,
                    "duplicate": result.duplicate,
                    "details": result.details,
                    "summary": result.summary,
                }

            return {
                "game": game,
                "results": formatted_results,
                "timestamp": __import__("datetime").datetime.now().isoformat(),
            }
    except Exception as e:
        logger.error(f"签到失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/account/{account_id}")
async def sign_account(account_id: int, game: Literal["arknights", "endfield", "all"] = "all"):
    """为指定账号执行签到

    Args:
        account_id: 账号 ID
        game: 游戏类型

    Returns:
        签到结果
    """
    async with db.get_session() as session:
        from sqlalchemy import select

        stmt = select(User).where(User.id == account_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="账号不存在")

        if not user.enabled:
            raise HTTPException(status_code=400, detail="账号未启用")

        try:
            sign_result = await sign_user(user, session, game)

            return {
                "account_id": account_id,
                "account_name": user.name,
                "game": game,
                "total": sign_result.total,
                "success": sign_result.success,
                "failed": sign_result.failed,
                "duplicate": sign_result.duplicate,
                "details": sign_result.details,
                "summary": sign_result.summary,
                "timestamp": __import__("datetime").datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"账号 {user.name} 签到失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_sign_status():
    """获取签到状态"""
    async with db.get_session() as session:
        from sqlalchemy import select, func
        from models import SignRecord

        # 获取今日签到统计
        today = __import__("datetime").datetime.now().date()

        stmt = select(
            func.count().label("total"),
            func.sum(func.cast(SignRecord.status == "success", __import__("sqlalchemy").Integer)).label("success"),
            func.sum(func.cast(SignRecord.status == "failed", __import__("sqlalchemy").Integer)).label("failed"),
            func.sum(func.cast(SignRecord.status == "duplicate", __import__("sqlalchemy").Integer)).label("duplicate"),
        ).where(
            func.date(SignRecord.sign_time) == today
        )

        result = await session.execute(stmt)
        row = result.one()

        return {
            "date": today.isoformat(),
            "total": row.total or 0,
            "success": row.success or 0,
            "failed": row.failed or 0,
            "duplicate": row.duplicate or 0,
        }


@router.get("/schedule")
async def get_schedule():
    """获取定时任务配置"""
    from config import config
    from scheduler import job_manager

    ark_job = job_manager.get_next_run_time("daily_arknights_sign")
    end_job = job_manager.get_next_run_time("daily_endfield_sign")

    return {
        "arknights": {
            "time": config.scheduler.arknights_sign_time,
            "next_run": ark_job.isoformat() if ark_job else None,
        },
        "endfield": {
            "time": config.scheduler.endfield_sign_time,
            "next_run": end_job.isoformat() if end_job else None,
        },
        "timezone": config.scheduler.timezone,
    }
