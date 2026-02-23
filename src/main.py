"""森空岛自动签到系统

独立的森空岛签到服务，支持明日方舟和终末地自动签到。
"""

import asyncio
import signal
from pathlib import Path

from config import config, accounts_config, AccountConfig, get_data_dir
from database import db
from models import User
from utils import setup_logger
from utils.logger import logger
from scheduler import job_manager


class SklandAutoSign:
    """森空岛自动签到应用"""

    def __init__(self):
        self._running = False
        self._shutdown_event = asyncio.Event()
        self._web_server = None

    async def initialize(self):
        """初始化应用"""
        # 设置日志
        setup_logger()
        logger.info(f"启动 {config.app.name} v{config.app.version}")

        # 初始化数据库
        logger.info("初始化数据库...")
        await db.init()

        # 加载账号配置
        await self._load_accounts()

        logger.info("应用初始化完成")

    async def _load_accounts(self):
        """从环境变量加载账号"""
        accounts = accounts_config.get_accounts()

        if not accounts:
            logger.warning("未配置任何账号")
            logger.info("请在 .env 文件中设置账号环境变量，或使用 Web 界面添加")
            return

        async with db.get_session() as session:
            from sqlalchemy import select

            # 获取现有账号
            stmt = select(User)
            result = await session.execute(stmt)
            existing_users = {user.name: user for user in result.scalars().all()}

            # 更新或添加账号
            for account in accounts:
                if account.name in existing_users:
                    # 更新现有账号
                    user = existing_users[account.name]
                    user.enabled = account.enabled
                    if account.token:
                        user.token = account.token
                    if account.cred:
                        user.cred = account.cred
                    if account.cred_token:
                        user.cred_token = account.cred_token
                    user.remark = account.remark
                    logger.info(f"更新账号: {account.name}")
                else:
                    # 添加新账号
                    user = User(
                        name=account.name,
                        enabled=account.enabled,
                        token=account.token,
                        cred=account.cred,
                        cred_token=account.cred_token,
                        remark=account.remark,
                    )
                    session.add(user)
                    logger.info(f"添加账号: {account.name}")

        logger.info(f"已加载 {len(accounts)} 个账号配置")

    async def start(self):
        """启动应用"""
        if self._running:
            return

        self._running = True
        self._shutdown_event.clear()

        # 启动定时任务
        job_manager.start()

        # 如果启用了 Web 服务
        if config.web.enabled:
            await self._start_web_server()

        logger.info("应用已启动，按 Ctrl+C 停止")

        # 等待关闭信号
        await self._shutdown_event.wait()

    async def _start_web_server(self):
        """启动 Web 服务器"""
        import uvicorn

        from api import app

        config = uvicorn.Config(
            app,
            host=config.web.host,
            port=config.web.port,
            log_level="info",
        )
        server = uvicorn.Server(config)
        self._web_server = server

        # 在后台启动 Web 服务器
        asyncio.create_task(server.serve())
        logger.info(f"Web 服务已启动: http://{config.web.host}:{config.web.port}")

    async def stop(self):
        """停止应用"""
        if not self._running:
            return

        logger.info("正在停止应用...")
        self._running = False
        self._shutdown_event.set()

        # 停止 Web 服务器
        if self._web_server:
            self._web_server.should_exit = True

        # 停止定时任务
        job_manager.shutdown()

        # 关闭数据库
        await db.close()

        logger.info("应用已停止")

    async def run_once(self, game_type: str = "all"):
        """运行一次签到（不启动定时任务）

        Args:
            game_type: 游戏类型 ("arknights", "endfield", "all")
        """
        await self.initialize()

        from core.sign_service import sign_all_users

        async with db.get_session() as session:
            results = await sign_all_users(session, game_type)

            # 输出结果
            for user_name, result in results.items():
                logger.info(f"\n{result.summary}")
                for nickname, detail in result.details.items():
                    logger.info(f"  {nickname}: {detail}")

        await db.close()


async def main():
    """主函数"""
    app = SklandAutoSign()

    # 设置信号处理
    loop = asyncio.get_running_loop()

    def signal_handler():
        app._shutdown_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    try:
        await app.initialize()
        await app.start()
    except asyncio.CancelledError:
        pass
    finally:
        await app.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
