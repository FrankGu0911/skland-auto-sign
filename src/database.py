"""数据库连接模块

使用 SQLAlchemy 管理数据库连接。
"""

from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from config import config, get_data_dir


class Base(DeclarativeBase):
    """数据库模型基类"""
    pass


class Database:
    """数据库管理类"""

    def __init__(self):
        self._engine = None
        self._session_factory = None

    def get_url(self) -> str:
        """获取数据库连接 URL"""
        db_config = config.database

        if db_config.type == "sqlite":
            db_path = db_config.get_sqlite_path()
            if db_path and not db_path.is_absolute():
                # 相对路径，需要加上项目根目录
                db_path = get_data_dir().parent / db_path
            db_path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite+aiosqlite:///{db_path}"
        elif db_config.type == "postgresql":
            return db_config.url
        else:
            raise ValueError(f"不支持的数据库类型: {db_config.type}")

    async def init(self):
        """初始化数据库连接"""
        url = self.get_url()
        self._engine = create_async_engine(
            url,
            echo=config.app.debug,
            future=True,
        )

        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # 导入所有模型
        from models import user, character, sign_record

        # 创建表
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self):
        """关闭数据库连接"""
        if self._engine:
            await self._engine.dispose()

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话

        Yields:
            AsyncSession: 数据库会话
        """
        if self._session_factory is None:
            raise RuntimeError("数据库未初始化，请先调用 init()")

        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def get_scoped_session(self) -> AsyncSession:
        """获取一个作用域会话（需要手动关闭）"""
        if self._session_factory is None:
            raise RuntimeError("数据库未初始化，请先调用 init()")
        return self._session_factory()


# 全局数据库实例
db = Database()
