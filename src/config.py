"""配置管理模块

使用 Pydantic Settings 管理应用配置，支持从环境变量和 .env 文件加载。
"""

import os
from pathlib import Path
from typing import Literal
from itertools import product

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseModel):
    """应用配置"""
    name: str = "Skland Auto Sign"
    version: str = "1.0.0"
    debug: bool = False


class DatabaseConfig(BaseSettings):
    """数据库配置"""
    type: Literal["sqlite", "postgresql"] = "sqlite"
    url: str = "sqlite:///data/skland.db"

    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def get_sqlite_path(self) -> Path | None:
        """获取 SQLite 数据库文件路径"""
        if self.type == "sqlite" and self.url.startswith("sqlite:///"):
            # 去掉 "sqlite:///" 前缀
            path_str = self.url[12:]
            # 总是返回相对路径
            return Path("data/skland.db")
        return None


class SchedulerConfig(BaseSettings):
    """定时任务配置"""
    arknights_sign_time: str = "00:15"
    endfield_sign_time: str = "00:20"
    timezone: str = "Asia/Shanghai"
    random_delay: int = 300  # 随机延迟秒数

    model_config = SettingsConfigDict(
        env_prefix="SCHEDULER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class LoggingConfig(BaseSettings):
    """日志配置"""
    level: str = "INFO"
    dir: str = "data/logs"
    retention: str = "30 days"
    rotation: str = "1 day"

    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class WebConfig(BaseSettings):
    """Web API 配置"""
    enabled: bool = False
    host: str = "0.0.0.0"
    port: int = 8080

    model_config = SettingsConfigDict(
        env_prefix="WEB_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class Config(BaseModel):
    """应用总配置"""
    app: AppConfig = Field(default_factory=AppConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    web: WebConfig = Field(default_factory=WebConfig)


class AccountConfig(BaseModel):
    """账号配置"""
    name: str
    enabled: bool = True
    token: str = ""
    cred: str = ""
    cred_token: str = ""
    remark: str = ""


class AccountsConfig(BaseSettings):
    """账号配置集合（从环境变量加载）

    支持的环境变量格式：
    - ACCOUNTS_1_NAME="账号1"
    - ACCOUNTS_1_ENABLED=true
    - ACCOUNTS_1_TOKEN=xxx
    - ACCOUNTS_1_CRED=xxx
    - ACCOUNTS_1_CRED_TOKEN=xxx
    - ACCOUNTS_1_REMARK=主账号

    - ACCOUNTS_2_NAME="账号2"
    - ACCOUNTS_2_TOKEN=yyy
    ...

    或者使用 JSON 格式：
    - ACCOUNTS_JSON='[{"name":"账号1","token":"xxx"}]'
    """

    # 使用 JSON 字符串存储所有账号（优先级高于单独的环境变量）
    accounts_json: str = ""

    model_config = SettingsConfigDict(
        env_prefix="ACCOUNTS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def get_accounts(self) -> list[AccountConfig]:
        """获取账号列表"""
        import json

        # 优先使用 JSON 格式
        if self.accounts_json:
            try:
                data = json.loads(self.accounts_json)
                return [AccountConfig(**acc) for acc in data]
            except (json.JSONDecodeError, TypeError):
                pass

        # 从单独的环境变量解析
        accounts = []
        index = 1
        while True:
            prefix = f"ACCOUNTS_{index}_"
            name = os.getenv(f"{prefix}NAME")
            if not name:
                break

            account = AccountConfig(
                name=name,
                enabled=os.getenv(f"{prefix}ENABLED", "true").lower() in ("true", "1", "yes"),
                token=os.getenv(f"{prefix}TOKEN", ""),
                cred=os.getenv(f"{prefix}CRED", ""),
                cred_token=os.getenv(f"{prefix}CRED_TOKEN", ""),
                remark=os.getenv(f"{prefix}REMARK", ""),
            )
            accounts.append(account)
            index += 1

        return accounts


def load_config() -> Config:
    """加载配置

    从环境变量和 .env 文件加载配置

    Returns:
        Config: 配置对象
    """
    return Config(
        app=AppConfig(),
        database=DatabaseConfig(),
        scheduler=SchedulerConfig(),
        logging=LoggingConfig(),
        web=WebConfig(),
    )


def load_accounts() -> AccountsConfig:
    """加载账号配置

    从环境变量和 .env 文件加载账号配置

    Returns:
        AccountsConfig: 账号配置对象
    """
    return AccountsConfig()


def get_project_root() -> Path:
    """获取项目根目录"""
    try:
        import inspect
        frame = inspect.currentframe()
        if frame is not None:
            # 向上查找调用栈，找到 config.py 文件
            while frame:
                if frame.f_code.co_filename and "config.py" in frame.f_code.co_filename:
                    root_dir = Path(frame.f_code.co_filename).parent.parent
                    break
                frame = frame.f_back
            else:
                root_dir = Path.cwd()
        else:
            root_dir = Path.cwd()
    except:
        root_dir = Path.cwd()

    return root_dir


def get_data_dir() -> Path:
    """获取数据目录路径"""
    root_dir = get_project_root()
    data_dir = root_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


# 全局配置实例
config = load_config()
accounts_config = load_accounts()
