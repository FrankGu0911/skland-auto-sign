"""用户模型"""

from sqlalchemy import String, Text, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class User(Base):
    """用户模型（森空岛账号）"""
    __tablename__ = "skland_user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, name="id")
    """用户 ID（内部主键）"""

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, name="name")
    """用户名称（用于标识账号）"""

    enabled: Mapped[bool] = mapped_column(Boolean, default=True, name="enabled")
    """是否启用签到"""

    token: Mapped[str] = mapped_column(Text, nullable=True, default="", name="token")
    """森空岛 access_token（用于刷新 cred）"""

    cred: Mapped[str] = mapped_column(Text, nullable=True, default="", name="cred")
    """森空岛登录凭证"""

    cred_token: Mapped[str] = mapped_column(Text, nullable=True, default="", name="cred_token")
    """森空岛登录凭证 token"""

    user_id: Mapped[str] = mapped_column(Text, nullable=True, default="", name="user_id")
    """森空岛用户 ID"""

    remark: Mapped[str] = mapped_column(Text, nullable=True, default="", name="remark")
    """备注信息"""

    def __repr__(self) -> str:
        return f"<User(id={self.id}, name={self.name}, enabled={self.enabled})>"
