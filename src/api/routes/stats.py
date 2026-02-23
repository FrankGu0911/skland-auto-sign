"""统计信息 API"""

from datetime import datetime, date, timedelta
from typing import List, Dict

from fastapi import APIRouter, Query
from pydantic import BaseModel

from database import db
from models import User, Character, SignRecord
from utils.logger import logger

router = APIRouter()


class OverviewStats(BaseModel):
    """概览统计"""
    total_users: int
    enabled_users: int
    total_characters: int
    today_sign: dict


class GameStats(BaseModel):
    """游戏统计"""
    game_type: str
    total_characters: int
    today_success: int
    today_failed: int
    today_duplicate: int
    success_rate: float


class DailyStats(BaseModel):
    """每日统计"""
    date: str
    total: int
    success: int
    failed: int
    duplicate: int


class UserStats(BaseModel):
    """用户统计"""
    user_id: int
    user_name: str
    character_count: int
    total_sign: int
    success_sign: int
    last_sign_time: datetime | None


@router.get("/overview")
async def get_overview():
    """获取概览统计 - 按角色维度计算今日签到"""
    async with db.get_session() as session:
        from sqlalchemy import select, func, cast, Integer

        # 用户统计
        user_stmt = select(
            func.count(User.id).label("total"),
            func.sum(func.cast(User.enabled == True, Integer)).label("enabled")
        )
        user_result = await session.execute(user_stmt)
        user_row = user_result.one()

        # 角色统计
        char_stmt = select(func.count(Character.id))
        char_result = await session.execute(char_stmt)
        total_characters = char_result.scalar()

        # 今日签到统计 - 按角色维度
        today = date.today()

        # 获取今日已签到的角色（去重）
        signed_char_stmt = select(func.count(func.distinct(SignRecord.character_id))).where(
            func.date(SignRecord.sign_time) == today
        )
        signed_char_result = await session.execute(signed_char_stmt)
        signed_count = signed_char_result.scalar() or 0

        return OverviewStats(
            total_users=user_row.total or 0,
            enabled_users=user_row.enabled or 0,
            total_characters=total_characters or 0,
            today_sign={
                "date": today.isoformat(),
                "total": total_characters or 0,
                "signed": signed_count,
                "unsigned": (total_characters or 0) - signed_count,
                "rate": f"{signed_count}/{total_characters or 1}" if total_characters else "0/0",
            }
        )


@router.get("/games", response_model=List[GameStats])
async def get_game_stats(days: int = Query(30, ge=1, le=365, description="统计天数")):
    """获取游戏统计"""
    async with db.get_session() as session:
        from sqlalchemy import select, func, cast, Integer, and_

        start_date = date.today() - timedelta(days=days)

        stats = []

        # 明日方舟统计
        ark_char_stmt = select(func.count(Character.id)).where(Character.app_name == "明日方舟")
        ark_char_result = await session.execute(ark_char_stmt)
        ark_char_count = ark_char_result.scalar()

        ark_sign_stmt = select(
            func.count(SignRecord.id).label("total"),
            func.sum(func.cast(SignRecord.status == "success", Integer)).label("success"),
            func.sum(func.cast(SignRecord.status == "failed", Integer)).label("failed"),
            func.sum(func.cast(SignRecord.status == "duplicate", Integer)).label("duplicate"),
        ).where(
            and_(
                SignRecord.game_type == "arknights",
                func.date(SignRecord.sign_time) >= start_date
            )
        )
        ark_sign_result = await session.execute(ark_sign_stmt)
        ark_sign_row = ark_sign_result.one()

        stats.append(GameStats(
            game_type="arknights",
            total_characters=ark_char_count or 0,
            today_success=ark_sign_row.success or 0,
            today_failed=ark_sign_row.failed or 0,
            today_duplicate=ark_sign_row.duplicate or 0,
            success_rate=(ark_sign_row.success / ark_sign_row.total * 100) if ark_sign_row.total else 0,
        ))

        # 终末地统计
        end_char_stmt = select(func.count(Character.id)).where(Character.app_name == "终末地")
        end_char_result = await session.execute(end_char_stmt)
        end_char_count = end_char_result.scalar()

        end_sign_stmt = select(
            func.count(SignRecord.id).label("total"),
            func.sum(func.cast(SignRecord.status == "success", Integer)).label("success"),
            func.sum(func.cast(SignRecord.status == "failed", Integer)).label("failed"),
            func.sum(func.cast(SignRecord.status == "duplicate", Integer)).label("duplicate"),
        ).where(
            and_(
                SignRecord.game_type == "endfield",
                func.date(SignRecord.sign_time) >= start_date
            )
        )
        end_sign_result = await session.execute(end_sign_stmt)
        end_sign_row = end_sign_result.one()

        stats.append(GameStats(
            game_type="endfield",
            total_characters=end_char_count or 0,
            today_success=end_sign_row.success or 0,
            today_failed=end_sign_row.failed or 0,
            today_duplicate=end_sign_row.duplicate or 0,
            success_rate=(end_sign_row.success / end_sign_row.total * 100) if end_sign_row.total else 0,
        ))

        return stats


@router.get("/daily", response_model=List[DailyStats])
async def get_daily_stats(
    days: int = Query(7, ge=1, le=90, description="统计天数")
):
    """获取每日统计"""
    async with db.get_session() as session:
        from sqlalchemy import select, func, desc
        from datetime import timedelta

        stats = []
        start_date = date.today() - timedelta(days=days - 1)

        for i in range(days):
            current_date = start_date + timedelta(days=i)

            stmt = select(
                func.count(SignRecord.id).label("total"),
                func.sum(func.cast(SignRecord.status == "success", Integer)).label("success"),
                func.sum(func.cast(SignRecord.status == "failed", Integer)).label("failed"),
                func.sum(func.cast(SignRecord.status == "duplicate", Integer)).label("duplicate"),
            ).where(func.date(SignRecord.sign_time) == current_date)

            result = await session.execute(stmt)
            row = result.one()

            stats.append(DailyStats(
                date=current_date.isoformat(),
                total=row.total or 0,
                success=row.success or 0,
                failed=row.failed or 0,
                duplicate=row.duplicate or 0,
            ))

        return stats


@router.get("/users", response_model=List[UserStats])
async def get_user_stats():
    """获取用户统计"""
    async with db.get_session() as session:
        from sqlalchemy import select, desc

        # 子查询：每个用户最后一次签到时间
        last_sign_stmt = select(
            SignRecord.user_id,
            func.max(SignRecord.sign_time).label("last_sign")
        ).group_by(SignRecord.user_id).subquery()

        # 主查询
        stmt = select(
            User.id,
            User.name,
            func.count(Character.id).label("char_count"),
            func.count(SignRecord.id).label("total_sign"),
            func.sum(func.cast(SignRecord.status == "success", func.INTEGER)).label("success_sign"),
            last_sign_stmt.c.last_sign,
        ).outerjoin(
            Character, User.id == Character.user_id
        ).outerjoin(
            last_sign_stmt, User.id == last_sign_stmt.c.user_id
        ).group_by(
            User.id, User.name, last_sign_stmt.c.last_sign
        ).order_by(
            desc(func.count(Character.id))
        )

        result = await session.execute(stmt)
        rows = result.all()

        return [
            UserStats(
                user_id=row.id,
                user_name=row.name,
                character_count=row.char_count,
                total_sign=row.total_sign,
                success_sign=row.success_sign,
                last_sign_time=row.last_sign,
            )
            for row in rows
        ]


@router.get("/rewards")
async def get_rewards_stats(
    days: int = Query(30, ge=1, le=365, description="统计天数")
):
    """获取奖励统计"""
    async with db.get_session() as session:
        from sqlalchemy import select, func
        from datetime import timedelta

        start_date = datetime.now() - timedelta(days=days)

        # 按游戏类型统计成功签到次数
        stmt = select(
            SignRecord.game_type,
            func.count(SignRecord.id).label("count")
        ).where(
            SignRecord.status == "success"
        ).group_by(
            SignRecord.game_type
        )

        result = await session.execute(stmt)
        rows = result.all()

        return {
            "period_days": days,
            "rewards": {
                row.game_type: row.count
                for row in rows
            }
        }
