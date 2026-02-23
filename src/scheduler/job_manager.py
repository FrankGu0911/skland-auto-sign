"""定时任务管理器

使用 APScheduler 管理定时签到任务。
"""

import random
from datetime import time
from typing import Literal

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import config
from database import db
from utils.logger import logger
from utils.decorators import refresh_cred_token_with_error_return, refresh_access_token_with_error_return
from models import User
from schemas import CRED, ArkSignResponse, EndfieldSignResponse
from core import SklandAPI
from core.sign_service import sign_all_users, bind_characters


class JobManager:
    """定时任务管理器"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone=config.scheduler.timezone)

    def start(self):
        """启动定时任务"""
        # 解析签到时间
        ark_hour, ark_minute = map(int, config.scheduler.arknights_sign_time.split(":"))
        end_hour, end_minute = map(int, config.scheduler.endfield_sign_time.split(":"))

        # 添加明日方舟签到任务
        self.scheduler.add_job(
            self._run_arknights_sign,
            trigger=CronTrigger(hour=ark_hour, minute=ark_minute),
            id="daily_arknights_sign",
            name="明日方舟每日签到",
            replace_existing=True,
        )

        # 添加终末地签到任务
        self.scheduler.add_job(
            self._run_endfield_sign,
            trigger=CronTrigger(hour=end_hour, minute=end_minute),
            id="daily_endfield_sign",
            name="终末地每日签到",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info(f"定时任务已启动")
        logger.info(f"明日方舟签到时间: {config.scheduler.arknights_sign_time}")
        logger.info(f"终末地签到时间: {config.scheduler.endfield_sign_time}")

    def shutdown(self):
        """关闭定时任务"""
        self.scheduler.shutdown()
        logger.info("定时任务已关闭")

    @staticmethod
    def _get_random_delay() -> int:
        """获取随机延迟时间"""
        if config.scheduler.random_delay > 0:
            return random.randint(0, config.scheduler.random_delay)
        return 0

    @staticmethod
    async def _run_arknights_sign():
        """执行明日方舟签到"""
        logger.info("开始执行明日方舟每日签到")

        async with db.get_session() as session:
            results = await sign_all_users(session, "arknights")

            # 输出结果
            for user_name, result in results.items():
                logger.info(f"\n{result.summary}")
                for nickname, detail in result.details.items():
                    logger.info(f"  {nickname}: {detail}")

        logger.info("明日方舟每日签到完成")

    @staticmethod
    async def _run_endfield_sign():
        """执行终末地签到"""
        logger.info("开始执行终末地每日签到")

        async with db.get_session() as session:
            results = await sign_all_users(session, "endfield")

            # 输出结果
            for user_name, result in results.items():
                logger.info(f"\n{result.summary}")
                for nickname, detail in result.details.items():
                    logger.info(f"  {nickname}: {detail}")

        logger.info("终末地每日签到完成")

    async def run_arknights_sign_now(self):
        """立即执行明日方舟签到"""
        await self._run_arknights_sign()

    async def run_endfield_sign_now(self):
        """立即执行终末地签到"""
        await self._run_endfield_sign()

    async def run_all_sign_now(self):
        """立即执行所有签到"""
        await self._run_arknights_sign()
        await self._run_endfield_sign()

    def get_jobs(self):
        """获取所有任务"""
        return self.scheduler.get_jobs()

    def get_next_run_time(self, job_id: str):
        """获取任务下次运行时间"""
        job = self.scheduler.get_job(job_id)
        if job:
            return job.next_run_time
        return None


# 全局任务管理器实例
job_manager = JobManager()
