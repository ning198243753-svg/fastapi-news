

from datetime import datetime

from pydantic import Field
from sqlalchemy import DateTime, ForeignKey, Index, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class History(Base):
    __tablename__ = "history"
    __table_args__ = (
        UniqueConstraint("user_id", "news_id", name="unique_history"),
        Index("idx_history_user_id", "user_id"),
        Index("idx_history_news_id", "news_id"),
    )
    id:Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))
    news_id: Mapped[int] = mapped_column(Integer, ForeignKey("news.id"))
    view_time: Mapped[datetime] = mapped_column(DateTime, default=func.now(),insert_default=func.now())
     