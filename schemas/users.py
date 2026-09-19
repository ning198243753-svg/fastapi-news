from typing import Optional

from pydantic import BaseModel, Field, field_validator

class UserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, password: str) -> str:
        # bcrypt limits the encoded password to 72 UTF-8 bytes.
        if len(password.encode("utf-8")) > 72:
            raise ValueError("密码编码后不能超过 72 字节")
        return password

class UserInfoBaseModel(BaseModel):
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    avatar: Optional[str] = Field(None, max_length=255, description="头像URL")
    gender: Optional[str] = Field(None, max_length=10, description="性别")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")
    model_config = {
                "from_attributes": True,
            }

class UserInfoResponse(UserInfoBaseModel):
    id: int
    username: str
    
class UserDataResponse(BaseModel):
    token: str 
    user_info: UserInfoResponse=Field(..., description="用户信息",alias="userInfo")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }

class UpdateUserInfo(BaseModel):
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    avatar: Optional[str] = Field(None, max_length=255, description="头像URL")
    gender: Optional[str] = Field(None, max_length=10, description="性别")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")
    phone:Optional[int] =Field(None)
    model_config = {
                    "from_attributes": True,
                }

class PasswordUpdate(BaseModel):
    new_password:str=Field(...,alias="newPassword")
    old_password:str=Field(...,alias="oldPassword")
