from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import Index, Integer, DateTime, ForeignKey, UniqueConstraint, func
from datetime import datetime
from .base import Base


class Favorite(Base):
    __tablename__ = "favorite"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))
    news_id: Mapped[int] = mapped_column(Integer, ForeignKey("news.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(),insert_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "news_id", name="unique_favorite"),
        Index("idx_favorite_user_id", "user_id"),
        Index("idx_favorite_news_id", "news_id"),
    )
