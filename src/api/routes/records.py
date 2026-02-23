"""签到记录 API"""

from datetime import datetime, date
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from database import db
from models import SignRecord, Character, User

router = APIRouter()


class SignRecordResponse(BaseModel):
    """签到记录响应"""
    id: int
    user_id: int
    user_name: str | None
    character_id: int
    character_nickname: str | None
    game_type: str
    sign_time: datetime
    status: str
    rewards: str
    error_message: str

    class Config:
        from_attributes = True


class SignRecordListResponse(BaseModel):
    """签到记录列表响应"""
    total: int
    page: int
    page_size: int
    records: List[SignRecordResponse]


@router.get("/", response_model=SignRecordListResponse)
async def get_records(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    game_type: Optional[str] = Query(None, description="游戏类型"),
    status: Optional[str] = Query(None, description="签到状态"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
):
    """获取签到记录列表"""
    async with db.get_session() as session:
        from sqlalchemy import select, func, desc

        # 构建查询，使用 JOIN 获取用户名和角色昵称
        stmt = (
            select(
                SignRecord,
                User.name.label("user_name"),
                Character.nickname.label("character_nickname"),
            )
            .join(User, SignRecord.user_id == User.id)
            .join(Character, SignRecord.character_id == Character.id)
        )

        # 添加过滤条件
        if game_type:
            stmt = stmt.where(SignRecord.game_type == game_type)
        if status:
            stmt = stmt.where(SignRecord.status == status)
        if user_id:
            stmt = stmt.where(SignRecord.user_id == user_id)
        if start_date:
            stmt = stmt.where(SignRecord.sign_time >= start_date)
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            stmt = stmt.where(SignRecord.sign_time <= end_datetime)

        # 获取总数（需要使用子查询避免 JOIN 影响计数）
        count_stmt = select(func.count(SignRecord.id))
        if game_type:
            count_stmt = count_stmt.where(SignRecord.game_type == game_type)
        if status:
            count_stmt = count_stmt.where(SignRecord.status == status)
        if user_id:
            count_stmt = count_stmt.where(SignRecord.user_id == user_id)
        if start_date:
            count_stmt = count_stmt.where(SignRecord.sign_time >= start_date)
        if end_date:
            count_stmt = count_stmt.where(SignRecord.sign_time <= end_datetime)

        total_result = await session.execute(count_stmt)
        total = total_result.scalar()

        # 分页和排序
        stmt = stmt.order_by(desc(SignRecord.sign_time))
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        # 执行查询
        result = await session.execute(stmt)
        rows = result.all()

        # 构建响应数据
        records = []
        for row in rows:
            record = row[0]
            records.append(
                SignRecordResponse(
                    id=record.id,
                    user_id=record.user_id,
                    user_name=row.user_name,
                    character_id=record.character_id,
                    character_nickname=row.character_nickname,
                    game_type=record.game_type,
                    sign_time=record.sign_time,
                    status=record.status,
                    rewards=record.rewards,
                    error_message=record.error_message,
                )
            )

        return SignRecordListResponse(
            total=total,
            page=page,
            page_size=page_size,
            records=records,
        )


@router.get("/{record_id}", response_model=SignRecordResponse)
async def get_record(record_id: int):
    """获取签到记录详情"""
    async with db.get_session() as session:
        from sqlalchemy import select

        stmt = select(SignRecord).where(SignRecord.id == record_id)
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()

        if not record:
            raise HTTPException(status_code=404, detail="记录不存在")

        return SignRecordResponse.model_validate(record)


@router.get("/user/{user_id}", response_model=List[SignRecordResponse])
async def get_user_records(
    user_id: int,
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
):
    """获取用户的签到记录"""
    async with db.get_session() as session:
        from sqlalchemy import select, desc

        stmt = select(SignRecord).where(SignRecord.user_id == user_id)
        stmt = stmt.order_by(desc(SignRecord.sign_time))
        stmt = stmt.limit(limit)

        result = await session.execute(stmt)
        records = result.scalars().all()

        return [SignRecordResponse.model_validate(record) for record in records]


@router.delete("/old")
async def delete_old_records(days: int = Query(30, ge=1, description="保留天数")):
    """删除旧的签到记录"""
    async with db.get_session() as session:
        from sqlalchemy import select, func
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days)

        # 获取要删除的记录数量
        count_stmt = select(func.count()).where(SignRecord.sign_time < cutoff_date)
        count_result = await session.execute(count_stmt)
        count = count_result.scalar() or 0

        # 删除记录
        stmt = select(SignRecord).where(SignRecord.sign_time < cutoff_date)
        result = await session.execute(stmt)
        records = result.scalars().all()

        for record in records:
            await session.delete(record)

        await session.commit()

        return {
            "message": f"已删除 {count} 条 {days} 天前的签到记录",
            "deleted_count": count,
        }
