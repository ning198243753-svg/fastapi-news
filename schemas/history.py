
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .base import NewsItemBase


class HistoryAddRequest(BaseModel):
    news_id: int = Field(...,gt=0,alias="newsId")

class HistoryAddResponse(BaseModel):
    id: int = Field(...,description="历史记录ID",alias="id")
    news_id: int = Field(...,description="新闻ID",alias="newsId")
    user_id: int = Field(...,description="用户ID",alias="userId")
    view_time: datetime = Field(...,description="浏览时间",alias="viewTime")
    model_config={
        "populate_by_name":True,
        "from_attributes":True
    }

class HistoryListInfo(NewsItemBase):
    view_time: Optional[datetime] = Field(None,description="浏览时间",alias="viewTime")
    model_config={
            "populate_by_name":True,
            "from_attributes":True
        }


class HistoryListResponse(BaseModel):
    list:list[HistoryListInfo]
    total: int = Field(...,description="总条数",alias="total")
    has_more: bool = Field(...,description="是否有更多",alias="hasMore")
    model_config={
        "populate_by_name":True,
        "from_attributes":True
    }

