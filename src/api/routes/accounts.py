"""账号管理 API"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from database import db
from models import User, Character
from schemas import CRED
from core import SklandLoginAPI
from utils.logger import logger

router = APIRouter()


class AccountCreate(BaseModel):
    """创建账号请求"""
    name: str = Field(..., description="账号名称")
    token: str = Field("", description="森空岛 access_token")
    cred: str = Field("", description="森空岛 cred")
    cred_token: str = Field("", description="森空岛 cred_token")
    remark: str = Field("", description="备注")


class AccountUpdate(BaseModel):
    """更新账号请求"""
    name: str | None = None
    token: str | None = None
    cred: str | None = None
    cred_token: str | None = None
    remark: str | None = None
    enabled: bool | None = None


class AccountResponse(BaseModel):
    """账号响应"""
    id: int
    name: str
    enabled: bool
    token: str
    cred: str
    cred_token: str
    user_id: str
    remark: str
    created_at: datetime | None = None
    character_count: int = 0


@router.get("/", response_model=List[AccountResponse])
async def list_accounts():
    """获取所有账号"""
    async with db.get_session() as session:
        from sqlalchemy import select, func

        # 获取账号列表
        stmt = select(User)
        result = await session.execute(stmt)
        users = result.scalars().all()

        # 获取每个账号的角色数量
        account_list = []
        for user in users:
            # 修复：使用 Character 模型而不是裸列
            char_stmt = select(func.count(Character.id)).where(Character.user_id == user.id)
            char_result = await session.execute(char_stmt)
            char_count = char_result.scalar() or 0

            account_list.append(AccountResponse(
                id=user.id,
                name=user.name,
                enabled=user.enabled,
                token=user.token[:20] + "..." if user.token and len(user.token) > 20 else user.token,
                cred=user.cred[:20] + "..." if user.cred and len(user.cred) > 20 else user.cred,
                cred_token=user.cred_token[:20] + "..." if user.cred_token and len(user.cred_token) > 20 else user.cred_token,
                user_id=user.user_id or "",
                remark=user.remark or "",
                character_count=char_count,
            ))

        return account_list


@router.post("/", response_model=AccountResponse)
async def create_account(account: AccountCreate):
    """创建账号"""
    async with db.get_session() as session:
        from sqlalchemy import select, func

        # 检查名称是否已存在
        stmt = select(User).where(User.name == account.name)
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="账号名称已存在")

        # 如果只提供了 token，自动获取 cred
        cred = account.cred
        cred_token = account.cred_token
        user_id = ""

        if account.token and not account.cred:
            try:
                grant_code = await SklandLoginAPI.get_grant_code(account.token, 0)
                cred_data = await SklandLoginAPI.get_cred(grant_code)
                cred = cred_data.cred
                cred_token = cred_data.token
                user_id = cred_data.userId or ""
                logger.info(f"账号 {account.name} 自动获取 cred 成功")
            except Exception as e:
                logger.error(f"账号 {account.name} 自动获取 cred 失败: {e}")
                raise HTTPException(status_code=400, detail=f"获取 cred 失败: {e}")

        # 创建账号
        user = User(
            name=account.name,
            enabled=True,
            token=account.token,
            cred=cred,
            cred_token=cred_token,
            user_id=user_id,
            remark=account.remark,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        # 自动同步角色
        character_count = 0
        if cred:
            try:
                from core.sign_service import bind_characters

                characters = await bind_characters(user, session)
                character_count = len(characters)
                logger.info(f"账号 {account.name} 自动同步角色成功，共 {character_count} 个角色")
            except Exception as e:
                logger.warning(f"账号 {account.name} 自动同步角色失败: {e}")
                # 不影响账号创建，继续返回

        # 获取角色数量
        char_stmt = select(func.count(Character.id)).where(Character.user_id == user.id)
        char_result = await session.execute(char_stmt)
        character_count = char_result.scalar() or 0

        return AccountResponse(
            id=user.id,
            name=user.name,
            enabled=user.enabled,
            token=user.token[:20] + "..." if user.token and len(user.token) > 20 else user.token,
            cred=user.cred[:20] + "..." if user.cred and len(user.cred) > 20 else user.cred,
            cred_token=user.cred_token[:20] + "..." if user.cred_token and len(user.cred_token) > 20 else user.cred_token,
            user_id=user.user_id or "",
            remark=user.remark or "",
            character_count=character_count,
        )


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(account_id: int):
    """获取账号详情"""
    async with db.get_session() as session:
        from sqlalchemy import select

        stmt = select(User).where(User.id == account_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="账号不存在")

        return AccountResponse(
            id=user.id,
            name=user.name,
            enabled=user.enabled,
            token=user.token,
            cred=user.cred,
            cred_token=user.cred_token,
            user_id=user.user_id or "",
            remark=user.remark or "",
            character_count=0,
        )


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(account_id: int, account: AccountUpdate):
    """更新账号"""
    async with db.get_session() as session:
        from sqlalchemy import select

        stmt = select(User).where(User.id == account_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="账号不存在")

        # 更新字段
        if account.name is not None:
            user.name = account.name
        if account.token is not None:
            user.token = account.token
        if account.cred is not None:
            user.cred = account.cred
        if account.cred_token is not None:
            user.cred_token = account.cred_token
        if account.remark is not None:
            user.remark = account.remark
        if account.enabled is not None:
            user.enabled = account.enabled

        await session.commit()
        await session.refresh(user)

        return AccountResponse(
            id=user.id,
            name=user.name,
            enabled=user.enabled,
            token=user.token,
            cred=user.cred,
            cred_token=user.cred_token,
            user_id=user.user_id or "",
            remark=user.remark or "",
            character_count=0,
        )


@router.delete("/{account_id}")
async def delete_account(account_id: int):
    """删除账号"""
    async with db.get_session() as session:
        from sqlalchemy import select

        stmt = select(User).where(User.id == account_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="账号不存在")

        await session.delete(user)
        await session.commit()

        return {"message": "账号已删除"}


@router.post("/{account_id}/refresh")
async def refresh_account_cred(account_id: int):
    """刷新账号 cred"""
    async with db.get_session() as session:
        from sqlalchemy import select

        stmt = select(User).where(User.id == account_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="账号不存在")

        if not user.token:
            raise HTTPException(status_code=400, detail="未配置 token，无法刷新 cred")

        try:
            grant_code = await SklandLoginAPI.get_grant_code(user.token, 0)
            cred_data = await SklandLoginAPI.get_cred(grant_code)
            user.cred = cred_data.cred
            user.cred_token = cred_data.token
            if cred_data.userId:
                user.user_id = cred_data.userId
            await session.commit()

            logger.info(f"账号 {user.name} cred 刷新成功")

            return {
                "message": "cred 刷新成功",
                "cred": user.cred[:20] + "...",
                "cred_token": user.cred_token[:20] + "...",
            }
        except Exception as e:
            logger.error(f"账号 {user.name} cred 刷新失败: {e}")
            raise HTTPException(status_code=400, detail=f"刷新 cred 失败: {e}")


@router.post("/{account_id}/sync")
async def sync_account_characters(account_id: int):
    """同步账号角色"""
    async with db.get_session() as session:
        from sqlalchemy import select

        stmt = select(User).where(User.id == account_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="账号不存在")

        try:
            from core.sign_service import bind_characters

            characters = await bind_characters(user, session)

            logger.info(f"账号 {user.name} 角色同步成功，共 {len(characters)} 个角色")

            return {
                "message": "角色同步成功",
                "count": len(characters),
                "characters": [
                    {
                        "uid": char.uid,
                        "nickname": char.nickname,
                        "app_name": char.app_name,
                    }
                    for char in characters
                ],
            }
        except Exception as e:
            logger.error(f"账号 {user.name} 角色同步失败: {e}")
            raise HTTPException(status_code=400, detail=f"同步角色失败: {e}")
