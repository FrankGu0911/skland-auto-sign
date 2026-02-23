"""签到记录模型"""

from datetime import datetime
from sqlalchemy import String, Text, Boolean, ForeignKey, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class SignRecord(Base):
    """签到记录模型"""
    __tablename__ = "skland_sign_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, name="id")
    """记录 ID"""

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("skland_user.id"), index=True, name="user_id")
    """关联的用户 ID"""

    character_id: Mapped[int] = mapped_column(Integer, ForeignKey("skland_characters.id"), index=True, name="character_id")
    """关联的角色 ID"""

    game_type: Mapped[str] = mapped_column(String(20), name="game_type")
    """游戏类型（arknights/endfield）"""

    sign_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, name="sign_time")
    """签到时间"""

    status: Mapped[str] = mapped_column(String(20), name="status")
    """签到状态（success/failed/duplicate）"""

    rewards: Mapped[str] = mapped_column(Text, nullable=True, default="", name="rewards")
    """奖励信息（JSON 格式）"""

    error_message: Mapped[str] = mapped_column(Text, nullable=True, default="", name="error_message")
    """错误信息"""

    def __repr__(self) -> str:
        return f"<SignRecord(id={self.id}, user_id={self.user_id}, game={self.game_type}, status={self.status})>"
