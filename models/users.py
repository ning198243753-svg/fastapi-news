from typing import Optional
from .base import CreateTimeMixin, CreateUpdateTimeMixin,Base
from sqlalchemy import Enum, ForeignKey, Index, Integer, String, DateTime,func
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column
from datetime import datetime


class user(Base, CreateUpdateTimeMixin):
    """
    用户信息表ORM模型
    """
    __tablename__ = "user"

    # 创建索引
    __table_args__ = (
        Index("username_UNIQUE", "username"),
        Index("phone_UNIQUE", "phone"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="用户ID")
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="用户名")
    password: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码（加密存储）")
    nickname: Mapped[Optional[str]] = mapped_column(String(50), comment="昵称")
    avatar: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="头像URL",
        default="https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png"
    )
    gender: Mapped[Optional[str]] = mapped_column(Enum("male", "female", "unknown"), comment="性别")
    bio: Mapped[Optional[str]] = mapped_column(String(500), comment="个人简介", default="这个人很懒，什么都没留下")
    phone: Mapped[Optional[str]] = mapped_column(String(20), unique=True, comment="手机号")



class UserToken(Base, CreateTimeMixin):
    """
    用户访问令牌表ORM模型
    """
    __tablename__ = "user_token"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="令牌ID")
    user_id: Mapped[int] = mapped_column(Integer,ForeignKey("user.id"),  nullable=False, comment="用户ID",)
    token: Mapped[str] = mapped_column(String(255), nullable=False, comment="访问令牌")
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="过期时间")
   
