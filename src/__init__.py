"""森空岛自动签到系统 - 包初始化"""

__version__ = "1.0.0"

# 导出核心模块
from config import config, load_config, get_data_dir, AccountsConfig
from database import db
from exception import RequestException, UnauthorizedException, LoginException

__all__ = [
    "config",
    "load_config",
    "get_data_dir",
    "AccountsConfig",
    "db",
    "RequestException",
    "UnauthorizedException",
    "LoginException",
]
