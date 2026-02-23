"""角色模型"""

from sqlalchemy import String, Text, Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Character(Base):
    """游戏角色模型"""
    __tablename__ = "skland_characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    """角色 ID（内部主键）"""

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("skland_user.id"), index=True, name="user_id")
    """关联的用户 ID"""

    uid: Mapped[str] = mapped_column(String(100), index=True, name="uid")
    """游戏角色 UID"""

    app_code: Mapped[str] = mapped_column(String(50), name="app_code")
    """APP Code（游戏标识）"""

    app_name: Mapped[str] = mapped_column(String(50), name="app_name")
    """APP 名称（如：明日方舟、终末地）"""

    channel_master_id: Mapped[str] = mapped_column(String(100), name="channel_master_id")
    """服务器 ID"""

    nickname: Mapped[str] = mapped_column(String(100), name="nickname")
    """角色昵称"""

    is_default: Mapped[bool] = mapped_column(Boolean, default=False, name="is_default")
    """是否为默认角色"""

    def __repr__(self) -> str:
        return f"<Character(uid={self.uid}, nickname={self.nickname}, app={self.app_name})>"
