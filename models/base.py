from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from datetime import datetime

class Base(DeclarativeBase):
    pass

class CreateTimeMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, insert_default=func.now(), comment="创建时间"
    )

class CreateUpdateTimeMixin(CreateTimeMixin):
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, insert_default=func.now(), onupdate=func.now(), comment="更新时间"
    )
