from datetime import datetime
from .base import NewsItemBase
from pydantic import BaseModel,Field

class FavoriteCheckResponse(BaseModel):
    is_favorite: bool = Field(...,description="是否收藏",alias="isFavorite")
    model_config={
        "populate_by_name":True
    }

class FavoriteAddRequest(BaseModel):
    news_id: int = Field(...,gt=0,alias="newsId")
    model_config={
        "populate_by_name":True
    }

class FavoriteAddResponse(BaseModel):
    id: int = Field(...,description="收藏ID",alias="id")
    user_id: int = Field(...,description="用户ID",alias="userId")
    news_id: int = Field(...,description="新闻ID",alias="newsId")
    created_at: datetime = Field(...,description="创建时间",alias="createTime")
    model_config={
        "populate_by_name":True,
        "from_attributes":True
    }

class NewsListResponse(NewsItemBase):
    favorite_id: int = Field(None,description="收藏ID",alias="favoriteId")
    favorite_time: datetime = Field(None,description="收藏时间",alias="favoriteTime")
    model_config={
        "populate_by_name":True,
        "from_attributes":True
    }   

class FavoriteListResponse(BaseModel):
    list:list[NewsListResponse]
    total: int = Field(...,description="总条数",alias="total")
    has_more: bool = Field(...,description="是否有更多",alias="hasMore")
    model_config={
        "populate_by_name":True,
        "from_attributes":True
    }

