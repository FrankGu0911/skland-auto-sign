"""装饰器模块

提供 Token 自动刷新装饰器。
"""

from collections.abc import Callable, Coroutine
from typing import TypeVar, ParamSpec, Concatenate

from utils.logger import logger
from core.skland_login import SklandLoginAPI
from exception import LoginException, RequestException, UnauthorizedException

P = ParamSpec("P")
R = TypeVar("R")


def refresh_cred_token_if_needed(func: Callable[Concatenate["User", P], Coroutine[None, None, R]]) -> Callable[Concatenate["User", P], Coroutine[None, None, R | None]]:
    """装饰器：如果 cred_token 失效，刷新后重试"""

    async def wrapper(user: "User", *args: P.args, **kwargs: P.kwargs) -> R | None:
        from models.user import User
        try:
            return await func(user, *args, **kwargs)
        except UnauthorizedException:
            try:
                new_token = await SklandLoginAPI.refresh_token(user.cred)
                user.cred_token = new_token
                logger.info(f"用户 {user.name} cred_token 失效，已自动刷新")
                return await func(user, *args, **kwargs)
            except (RequestException, LoginException, UnauthorizedException) as e:
                logger.error(f"用户 {user.name} 刷新 cred_token 失败: {e}")
        except RequestException as e:
            logger.error(f"用户 {user.name} 请求失败: {e}")

    return wrapper


def refresh_cred_token_with_error_return(func: Callable[Concatenate["User", P], Coroutine[None, None, R]]) -> Callable[Concatenate["User", P], Coroutine[None, None, R | str]]:
    """装饰器：如果 cred_token 失效，刷新后重试，失败时返回错误信息"""

    async def wrapper(user: "User", *args: P.args, **kwargs: P.kwargs) -> R | str:
        from models.user import User
        try:
            return await func(user, *args, **kwargs)
        except UnauthorizedException:
            try:
                new_token = await SklandLoginAPI.refresh_token(user.cred)
                user.cred_token = new_token
                logger.info(f"用户 {user.name} cred_token 失效，已自动刷新")
                return await func(user, *args, **kwargs)
            except (RequestException, LoginException, UnauthorizedException) as e:
                error_msg = f"接口请求失败, {e.args[0] if e.args else str(e)}"
                logger.error(f"用户 {user.name} {error_msg}")
                return error_msg
        except RequestException as e:
            error_msg = f"接口请求失败, {e.args[0] if e.args else str(e)}"
            logger.error(f"用户 {user.name} {error_msg}")
            return error_msg

    return wrapper


def refresh_access_token_if_needed(func: Callable[Concatenate["User", P], Coroutine[None, None, R]]) -> Callable[Concatenate["User", P], Coroutine[None, None, R | None]]:
    """装饰器：如果 access_token 失效（cred 失效），刷新后重试"""

    async def wrapper(user: "User", *args: P.args, **kwargs: P.kwargs) -> R | None:
        from models.user import User
        try:
            return await func(user, *args, **kwargs)
        except LoginException:
            if not user.token:
                logger.error(f"用户 {user.name} cred 失效，但未配置 token，无法自动刷新")
                return None

            try:
                from schemas import CRED
                grant_code = await SklandLoginAPI.get_grant_code(user.token, 0)
                new_cred = await SklandLoginAPI.get_cred(grant_code)
                user.cred = new_cred.cred
                user.cred_token = new_cred.token
                if new_cred.userId:
                    user.user_id = new_cred.userId
                logger.info(f"用户 {user.name} cred 失效，已自动刷新")
                return await func(user, *args, **kwargs)
            except (RequestException, LoginException, UnauthorizedException) as e:
                logger.error(f"用户 {user.name} 刷新 cred 失败: {e}")
        except RequestException as e:
            logger.error(f"用户 {user.name} 请求失败: {e}")

    return wrapper


def refresh_access_token_with_error_return(func: Callable[Concatenate["User", P], Coroutine[None, None, R]]) -> Callable[Concatenate["User", P], Coroutine[None, None, R | str]]:
    """装饰器：如果 access_token 失效（cred 失效），刷新后重试，失败时返回错误信息"""

    async def wrapper(user: "User", *args: P.args, **kwargs: P.kwargs) -> R | str:
        from models.user import User
        try:
            return await func(user, *args, **kwargs)
        except LoginException:
            if not user.token:
                error_msg = "cred 失效，但未配置 token，无法自动刷新"
                logger.error(f"用户 {user.name} {error_msg}")
                return error_msg

            try:
                from schemas import CRED
                grant_code = await SklandLoginAPI.get_grant_code(user.token, 0)
                new_cred = await SklandLoginAPI.get_cred(grant_code)
                user.cred = new_cred.cred
                user.cred_token = new_cred.token
                if new_cred.userId:
                    user.user_id = new_cred.userId
                logger.info(f"用户 {user.name} cred 失效，已自动刷新")
                return await func(user, *args, **kwargs)
            except (RequestException, LoginException, UnauthorizedException) as e:
                error_msg = f"接口请求失败, {e.args[0] if e.args else str(e)}"
                logger.error(f"用户 {user.name} {error_msg}")
                return error_msg
        except RequestException as e:
            error_msg = f"接口请求失败, {e.args[0] if e.args else str(e)}"
            logger.error(f"用户 {user.name} {error_msg}")
            return error_msg

    return wrapper
