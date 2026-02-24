"""签到服务模块

提供明日方舟和终末地的签到功能。
"""

import json
from datetime import datetime
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User, Character, SignRecord
from schemas import CRED, ArkSignResponse, EndfieldSignResponse
from core import SklandAPI
from exception import LoginException, RequestException, UnauthorizedException
from utils.logger import logger


class SignResult:
    """签到结果"""

    def __init__(self):
        self.total: int = 0
        self.success: int = 0
        self.failed: int = 0
        self.duplicate: int = 0
        self.details: dict[str, str] = {}

    def add_success(self, nickname: str, message: str):
        """添加成功记录"""
        self.success += 1
        self.total += 1
        self.details[nickname] = message

    def add_failed(self, nickname: str, error: str):
        """添加失败记录"""
        self.failed += 1
        self.total += 1
        self.details[nickname] = f"❌ 签到失败: {error}"

    def add_duplicate(self, nickname: str, message: str = "已签到 (无需重复签到)"):
        """添加重复签到记录"""
        self.duplicate += 1
        self.total += 1
        self.details[nickname] = f"ℹ️ {message}"

    def add_info(self, nickname: str, message: str):
        """添加信息记录"""
        self.total += 1
        self.details[nickname] = f"ℹ️ {message}"

    @property
    def summary(self) -> str:
        """获取摘要"""
        return (
            f"--- 签到结果概览 ---\n"
            f"总计处理: {self.total} 个\n"
            f"✅ 成功签到: {self.success} 个\n"
            f"ℹ️ 已签到: {self.duplicate} 个\n"
            f"❌ 签到失败: {self.failed} 个\n"
            f"⏰ 签到时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"--------------------"
        )


async def bind_characters(user: User, session: AsyncSession) -> list[Character]:
    """获取并更新用户绑定的角色"""
    cred = CRED(cred=user.cred, token=user.cred_token)
    binding_list = await SklandAPI.get_binding(cred)

    logger.info(f"用户 {user.name} 获取到 {len(binding_list)} 个游戏绑定")

    # 删除旧的角色
    stmt = select(Character).where(Character.user_id == user.id)
    result = await session.execute(stmt)
    old_characters = result.scalars().all()
    for old_char in old_characters:
        await session.delete(old_char)

    # 添加新角色
    characters = []
    for app in binding_list:
        app_code = app.get("appCode", "")
        app_name = _get_app_name(app_code)

        logger.info(f"处理游戏 {app_name} (app_code={app_code})")

        for character in app.get("bindingList", []):
            is_default = character.get("isDefault", False)

            # 处理普通角色
            if not character.get("roles"):
                char = Character(
                    user_id=user.id,
                    uid=str(character.get("uid", "")),
                    app_code=app_code,
                    app_name=app_name,
                    channel_master_id=str(character.get("channelMasterId", "")),
                    nickname=character.get("nickName", ""),
                    is_default=is_default,
                )
                session.add(char)
                characters.append(char)
                logger.info(f"  添加角色: {char.nickname} ({char.app_name})")

            # 处理有 roles 的角色（终末地）
            for role in character.get("roles", []):
                char = Character(
                    user_id=user.id,
                    uid=str(role.get("roleId", "")),
                    app_code=app_code,
                    app_name=app_name,
                    channel_master_id=str(role.get("serverId", "")),
                    nickname=role.get("nickname", ""),
                    is_default=role.get("isDefault", is_default),
                )
                session.add(char)
                characters.append(char)
                logger.info(f"  添加角色: {char.nickname} ({char.app_name})")

    await session.commit()
    logger.info(f"用户 {user.name} 角色同步完成，共 {len(characters)} 个角色")
    return characters


def _get_app_name(app_code: str) -> str:
    """获取 APP 名称"""
    app_names = {
        # 原始哈希值（兼容）
        "4ca99fa6b56cc2ba": "明日方舟",
        "be36d44aa36bfb5b": "终末地",
        # 新的简短名称
        "arknights": "明日方舟",
        "endfield": "终末地",
    }
    return app_names.get(app_code, "未知游戏")


async def do_arknights_sign(user: User, character: Character, session: AsyncSession) -> SignResult:
    """执行明日方舟签到（带自动重试）"""
    result = SignResult()
    retried = False  # 是否已重试过

    while True:
        try:
            cred = CRED(cred=user.cred, token=user.cred_token)
            sign_response = await SklandAPI.ark_sign(cred, character.uid, character.channel_master_id)

            # 保存签到记录
            awards_text = "\n".join(
                f"  {award.resource.name} x {award.count}"
                for award in sign_response.awards
            )
            record = SignRecord(
                user_id=user.id,
                character_id=character.id,
                game_type="arknights",
                status="success",
                rewards=json.dumps([{"name": a.resource.name, "count": a.count} for a in sign_response.awards]),
            )
            session.add(record)

            result.add_success(
                character.nickname,
                f"✅ 签到成功，获得了:\n📦{awards_text}"
            )
            logger.info(f"用户 {user.name} 角色 {character.nickname} 明日方舟签到成功")
            break

        except LoginException as e:
            # cred 失效，尝试刷新
            if user.token and not retried:
                logger.warning(f"用户 {user.name} 角色 {character.nickname} 明日方舟签到 cred 失效，尝试自动刷新...")
                try:
                    from core import SklandLoginAPI
                    grant_code = await SklandLoginAPI.get_grant_code(user.token, 0)
                    new_cred = await SklandLoginAPI.get_cred(grant_code)
                    user.cred = new_cred.cred
                    user.cred_token = new_cred.token
                    if new_cred.userId:
                        user.user_id = new_cred.userId
                    logger.info(f"用户 {user.name} cred 刷新成功，重试签到...")
                    retried = True
                    await session.commit()  # 保存新的 cred
                    continue
                except Exception as refresh_error:
                    logger.error(f"用户 {user.name} 刷新 cred 失败: {refresh_error}")
                    result.add_failed(character.nickname, f"cred 失效且刷新失败: {e}")
                    break
            else:
                result.add_failed(character.nickname, f"cred 失效（未配置 token 无法自动刷新）: {e}")
                logger.error(f"用户 {user.name} 角色 {character.nickname} 明日方舟签到失败 (LoginException): {e}")
                break

        except UnauthorizedException as e:
            # cred_token 失效，尝试刷新
            if not retried:
                logger.warning(f"用户 {user.name} 角色 {character.nickname} 明日方舟签到 cred_token 失效，尝试自动刷新...")
                try:
                    from core import SklandLoginAPI
                    new_token = await SklandLoginAPI.refresh_token(user.cred)
                    user.cred_token = new_token
                    logger.info(f"用户 {user.name} cred_token 刷新成功，重试签到...")
                    retried = True
                    await session.commit()  # 保存新的 cred_token
                    continue
                except Exception as refresh_error:
                    logger.error(f"用户 {user.name} 刷新 cred_token 失败: {refresh_error}")
                    result.add_failed(character.nickname, f"cred_token 失效且刷新失败: {e}")
                    break
            else:
                result.add_failed(character.nickname, f"cred_token 失效: {e}")
                logger.error(f"用户 {user.name} 角色 {character.nickname} 明日方舟签到失败 (UnauthorizedException): {e}")
                break

        except RequestException as e:
            error_msg = str(e)
            if "请勿重复签到" in error_msg:
                result.add_duplicate(character.nickname)
                record = SignRecord(
                    user_id=user.id,
                    character_id=character.id,
                    game_type="arknights",
                    status="duplicate",
                )
                session.add(record)
                logger.info(f"用户 {user.name} 角色 {character.nickname} 明日方舟已签到")
            # 对可能由认证问题导致的未知错误，尝试刷新 cred
            elif user.token and not retried and any(keyword in error_msg.lower() for keyword in ["认证", "授权", "登录", "token", "cred", "凭证", "未登录"]):
                logger.warning(f"用户 {user.name} 角色 {character.nickname} 明日方舟签到可能因认证问题失败，尝试自动刷新...")
                try:
                    from core import SklandLoginAPI
                    grant_code = await SklandLoginAPI.get_grant_code(user.token, 0)
                    new_cred = await SklandLoginAPI.get_cred(grant_code)
                    user.cred = new_cred.cred
                    user.cred_token = new_cred.token
                    if new_cred.userId:
                        user.user_id = new_cred.userId
                    logger.info(f"用户 {user.name} cred 刷新成功，重试签到...")
                    retried = True
                    await session.commit()  # 保存新的 cred
                    continue
                except Exception as refresh_error:
                    logger.error(f"用户 {user.name} 刷新 cred 失败: {refresh_error}")
                    result.add_failed(character.nickname, error_msg)
                    break
            else:
                result.add_failed(character.nickname, error_msg)
                logger.error(f"用户 {user.name} 角色 {character.nickname} 明日方舟签到失败: {e}")
            break

    return result


async def do_endfield_sign(user: User, character: Character, session: AsyncSession) -> SignResult:
    """执行终末地签到（带自动重试）"""
    result = SignResult()
    retried = False  # 是否已重试过

    while True:
        try:
            cred = CRED(cred=user.cred, token=user.cred_token)
            sign_response = await SklandAPI.endfield_sign(cred, character.uid, character.channel_master_id)

            # 保存签到记录
            awards_text = sign_response.award_summary
            record = SignRecord(
                user_id=user.id,
                character_id=character.id,
                game_type="endfield",
                status="success",
                rewards=json.dumps([{"id": a.id, "type": a.type} for a in sign_response.awardIds]),
            )
            session.add(record)

            result.add_success(
                character.nickname,
                f"✅ 签到成功，获得了:\n📦{awards_text}"
            )
            logger.info(f"用户 {user.name} 角色 {character.nickname} 终末地签到成功")
            break

        except LoginException as e:
            # cred 失效，尝试刷新
            if user.token and not retried:
                logger.warning(f"用户 {user.name} 角色 {character.nickname} 终末地签到 cred 失效，尝试自动刷新...")
                try:
                    from core import SklandLoginAPI
                    grant_code = await SklandLoginAPI.get_grant_code(user.token, 0)
                    new_cred = await SklandLoginAPI.get_cred(grant_code)
                    user.cred = new_cred.cred
                    user.cred_token = new_cred.token
                    if new_cred.userId:
                        user.user_id = new_cred.userId
                    logger.info(f"用户 {user.name} cred 刷新成功，重试签到...")
                    retried = True
                    await session.commit()  # 保存新的 cred
                    continue
                except Exception as refresh_error:
                    logger.error(f"用户 {user.name} 刷新 cred 失败: {refresh_error}")
                    result.add_failed(character.nickname, f"cred 失效且刷新失败: {e}")
                    break
            else:
                result.add_failed(character.nickname, f"cred 失效（未配置 token 无法自动刷新）: {e}")
                logger.error(f"用户 {user.name} 角色 {character.nickname} 终末地签到失败 (LoginException): {e}")
                break

        except UnauthorizedException as e:
            # cred_token 失效，尝试刷新
            if not retried:
                logger.warning(f"用户 {user.name} 角色 {character.nickname} 终末地签到 cred_token 失效，尝试自动刷新...")
                try:
                    from core import SklandLoginAPI
                    new_token = await SklandLoginAPI.refresh_token(user.cred)
                    user.cred_token = new_token
                    logger.info(f"用户 {user.name} cred_token 刷新成功，重试签到...")
                    retried = True
                    await session.commit()  # 保存新的 cred_token
                    continue
                except Exception as refresh_error:
                    logger.error(f"用户 {user.name} 刷新 cred_token 失败: {refresh_error}")
                    result.add_failed(character.nickname, f"cred_token 失效且刷新失败: {e}")
                    break
            else:
                result.add_failed(character.nickname, f"cred_token 失效: {e}")
                logger.error(f"用户 {user.name} 角色 {character.nickname} 终末地签到失败 (UnauthorizedException): {e}")
                break

        except RequestException as e:
            error_msg = str(e)
            if "请勿重复签到" in error_msg:
                result.add_duplicate(character.nickname)
                record = SignRecord(
                    user_id=user.id,
                    character_id=character.id,
                    game_type="endfield",
                    status="duplicate",
                )
                session.add(record)
                logger.info(f"用户 {user.name} 角色 {character.nickname} 终末地已签到")
            # 对可能由认证问题导致的未知错误，尝试刷新 cred
            elif user.token and not retried and any(keyword in error_msg.lower() for keyword in ["认证", "授权", "登录", "token", "cred", "凭证", "未登录"]):
                logger.warning(f"用户 {user.name} 角色 {character.nickname} 终末地签到可能因认证问题失败，尝试自动刷新...")
                try:
                    from core import SklandLoginAPI
                    grant_code = await SklandLoginAPI.get_grant_code(user.token, 0)
                    new_cred = await SklandLoginAPI.get_cred(grant_code)
                    user.cred = new_cred.cred
                    user.cred_token = new_cred.token
                    if new_cred.userId:
                        user.user_id = new_cred.userId
                    logger.info(f"用户 {user.name} cred 刷新成功，重试签到...")
                    retried = True
                    await session.commit()  # 保存新的 cred
                    continue
                except Exception as refresh_error:
                    logger.error(f"用户 {user.name} 刷新 cred 失败: {refresh_error}")
                    result.add_failed(character.nickname, error_msg)
                    break
            else:
                result.add_failed(character.nickname, error_msg)
                logger.error(f"用户 {user.name} 角色 {character.nickname} 终末地签到失败: {e}")
            break

    return result


async def sign_user(user: User, session: AsyncSession, game_type: Literal["arknights", "endfield", "all"] = "all", auto_sync: bool = True) -> SignResult:
    """为用户执行签到

    Args:
        user: 用户对象
        session: 数据库会话
        game_type: 游戏类型，"arknights" 只签到明日方舟，"endfield" 只签到终末地，"all" 签到全部
        auto_sync: 是否自动同步角色（如果用户没有角色）

    Returns:
        SignResult: 签到结果
    """
    result = SignResult()

    # 获取用户角色
    stmt = select(Character).where(Character.user_id == user.id)
    db_result = await session.execute(stmt)
    characters = db_result.scalars().all()

    # 如果没有角色且开启了自动同步，尝试同步
    if not characters and auto_sync:
        logger.info(f"用户 {user.name} 没有角色，尝试自动同步...")
        try:
            characters = await bind_characters(user, session)
        except Exception as e:
            logger.error(f"用户 {user.name} 自动同步角色失败: {e}")
            result.add_info("系统", f"⚠️ 没有找到游戏角色，请先在 Web 界面同步角色")
            return result

    # 再次检查
    if not characters:
        logger.warning(f"用户 {user.name} 没有可签到的角色")
        result.add_info("系统", f"⚠️ 没有找到可签到的游戏角色")
        return result

    logger.info(f"用户 {user.name} 开始签到，共 {len(characters)} 个角色")

    for character in characters:
        # 检查是否需要签到该游戏
        if game_type == "arknights" and character.app_name != "明日方舟":
            continue
        if game_type == "endfield" and character.app_name != "终末地":
            continue

        # 执行签到
        if character.app_name == "明日方舟":
            char_result = await do_arknights_sign(user, character, session)
        elif character.app_name == "终末地":
            char_result = await do_endfield_sign(user, character, session)
        else:
            logger.warning(f"未知游戏类型: {character.app_name}")
            continue

        result.total += char_result.total
        result.success += char_result.success
        result.failed += char_result.failed
        result.duplicate += char_result.duplicate
        result.details.update(char_result.details)

    await session.commit()
    return result


async def sign_all_users(session: AsyncSession, game_type: Literal["arknights", "endfield", "all"] = "all", auto_sync: bool = True) -> dict[str, SignResult]:
    """为所有启用的用户执行签到

    Args:
        session: 数据库会话
        game_type: 游戏类型
        auto_sync: 是否自动同步角色

    Returns:
        dict[str, SignResult]: 每个用户的签到结果
    """
    # 获取所有启用的用户
    stmt = select(User).where(User.enabled == True)
    result = await session.execute(stmt)
    users = result.scalars().all()

    if not users:
        logger.warning("数据库中没有启用的用户")
        return {}

    results = {}
    for user in users:
        logger.info(f"开始为用户 {user.name} 执行 {game_type} 签到")
        try:
            user_result = await sign_user(user, session, game_type, auto_sync)
            results[user.name] = user_result
        except Exception as e:
            logger.error(f"用户 {user.name} 签到过程出错: {e}")
            error_result = SignResult()
            error_result.failed = 1
            error_result.add_info("系统", f"❌ 签到过程出错: {e}")
            results[user.name] = error_result

    return results
