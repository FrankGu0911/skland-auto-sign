"""森空岛登录 API

从原项目复用并移除 NoneBot 依赖。
"""

import httpx

from schemas import CRED
from exception import RequestException


skland_app_code = "4ca99fa6b56cc2ba"
web_app_code = "be36d44aa36bfb5b"


class SklandLoginAPI:
    """森空岛登录 API"""

    _headers = {
        "User-Agent": "Skland/1.32.1 (com.hypergryph.skland; build:103201004; Android 33; ) Okhttp/4.11.0",
        "Accept-Encoding": "gzip",
        "Connection": "close",
    }

    @classmethod
    async def get_grant_code(cls, token: str, grant_type: int) -> str:
        """
        获取认证代码或 token。

        Args:
            token: 用户 token
            grant_type: 授权类型。0 返回森空岛认证代码(code)，1 返回官网通行证 token。

        Returns:
            grant_type 为 0 时返回森空岛认证代码(code)，grant_type 为 1 时返回官网通行证 token。
        """
        async with httpx.AsyncClient() as client:
            code = skland_app_code if grant_type == 0 else web_app_code
            response = await client.post(
                "https://as.hypergryph.com/user/oauth2/v2/grant",
                json={"appCode": code, "token": token, "type": grant_type},
                headers={**cls._headers},
            )
            if status := response.json().get("status"):
                if status != 0:
                    raise RequestException(f"使用 token 获得认证代码失败：{response.json().get('msg')}")
            return response.json()["data"]["code"] if grant_type == 0 else response.json()["data"]["token"]

    @classmethod
    async def get_cred(cls, grant_code: str) -> CRED:
        """通过认证代码获取 cred"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://zonai.skland.com/api/v1/user/auth/generate_cred_by_code",
                json={"code": grant_code, "kind": 1},
                headers={**cls._headers},
            )
            if status := response.json().get("status"):
                if status != 0:
                    raise RequestException(f"获得 cred 失败：{response.json().get('message')}")
            return CRED(**response.json().get("data"))

    @classmethod
    async def refresh_token(cls, cred: str) -> str:
        """刷新 cred_token"""
        async with httpx.AsyncClient() as client:
            refresh_url = "https://zonai.skland.com/api/v1/auth/refresh"
            try:
                response = await client.get(
                    refresh_url,
                    headers={**cls._headers, "cred": cred},
                )
                response.raise_for_status()
                if status := response.json().get("status"):
                    if status != 0:
                        raise RequestException(f"刷新 token 失败：{response.json().get('message')}")
                token = response.json().get("data").get("token")
                return token
            except httpx.HTTPError as e:
                raise RequestException(f"刷新 token 失败：{str(e)}")

    @classmethod
    async def get_scan(cls) -> str:
        """获取登录二维码"""
        async with httpx.AsyncClient() as client:
            get_scan_url = "https://as.hypergryph.com/general/v1/gen_scan/login"
            response = await client.post(
                get_scan_url,
                json={"appCode": skland_app_code},
            )
            if status := response.json().get("status"):
                if status != 0:
                    raise RequestException(f"获取登录二维码失败：{response.json().get('msg')}")
            return response.json()["data"]["scanId"]

    @classmethod
    async def get_scan_status(cls, scan_id: str) -> str:
        """获取二维码扫描状态"""
        async with httpx.AsyncClient() as client:
            get_scan_status_url = "https://as.hypergryph.com/general/v1/scan_status"
            response = await client.get(
                get_scan_status_url,
                params={"scanId": scan_id},
            )
            if status := response.json().get("status"):
                if status != 0:
                    raise RequestException(f"获取二维码 scanCode 失败：{response.json().get('msg')}")
            return response.json()["data"]["scanCode"]

    @classmethod
    async def get_token_by_scan_code(cls, scan_code: str) -> str:
        """通过扫描码获取 token"""
        async with httpx.AsyncClient() as client:
            get_token_by_scan_code_url = "https://as.hypergryph.com/user/auth/v1/token_by_scan_code"
            response = await client.post(
                get_token_by_scan_code_url,
                json={"scanCode": scan_code},
            )
            if status := response.json().get("status"):
                if status != 0:
                    raise RequestException(f"获取 token 失败：{response.json().get('msg')}")
            return response.json()["data"]["token"]
