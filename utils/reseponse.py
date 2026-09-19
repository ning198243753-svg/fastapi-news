from sqlalchemy import null

from schemas.users import UserDataResponse
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


def sucess_response(data: UserDataResponse=null, message: str = "Success"):
    """
    构建成功响应的工具函数
    :param data: 响应数据
    :param message: 响应消息
    :return: 成功响应字典
    """
    content = {
        "code": 200,
        "message": message,
        "data": data
    }
    
    return JSONResponse(content=jsonable_encoder(content))