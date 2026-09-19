from typing import Optional
from .base import Base,CreateUpdateTimeMixin
from sqlalchemy import Integer, String, Text, DateTime,func
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column
from datetime import datetime



class news_category(CreateUpdateTimeMixin,Base):
    __tablename__ = "news_category"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True,nullable=False, comment="分类ID")
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="分类名称")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, comment="排序方式")

class news(Base,CreateUpdateTimeMixin):
    __tablename__ = "news"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True,nullable=False, comment="新闻ID")
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="新闻标题")
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="新闻描述")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="新闻内容")
    image: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="新闻图片")
    author: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="作者")
    category_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="分类ID",index=True)
    views: Mapped[int] = mapped_column(Integer, nullable=False, comment="浏览量",insert_default=0,default=0)
    publish_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, insert_default=func.now(),default=func.now(), comment="发布时间",index=True)