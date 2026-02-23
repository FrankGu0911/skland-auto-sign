"""日志配置模块

使用 loguru 配置应用日志。
"""

import sys
from pathlib import Path
from loguru import logger

from config import config, get_data_dir


def setup_logger():
    """配置日志系统"""

    # 移除默认处理器
    logger.remove()

    # 控制台输出
    logger.add(
        sys.stdout,
        level=config.logging.level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # 文件输出
    log_dir = Path(config.logging.dir)
    if not log_dir.is_absolute():
        log_dir = get_data_dir() / config.logging.dir

    log_dir.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_dir / "app.log",
        level=config.logging.level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation=config.logging.rotation,
        retention=config.logging.retention,
        compression="zip",
        encoding="utf-8",
    )

    # 错误日志单独文件
    logger.add(
        log_dir / "error.log",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation=config.logging.rotation,
        retention=config.logging.retention,
        compression="zip",
        encoding="utf-8",
    )

    return logger
