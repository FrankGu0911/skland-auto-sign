"""CRED 数据模型"""

from dataclasses import dataclass


@dataclass
class CRED:
    """森空岛登录凭证"""
    cred: str
    """登录凭证"""

    token: str
    """登录凭证对应的 token"""

    userId: str | None = None
    """用户 ID"""
