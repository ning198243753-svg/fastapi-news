from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(...,description="用户输入",alias="message")
    model_config={
        "populate_by_name":True,
        "from_attributes":True
    }