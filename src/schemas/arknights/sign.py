"""明日方舟签到相关数据模型"""

from pydantic import BaseModel


class Resource(BaseModel):
    """资源"""
    name: str


class Award(BaseModel):
    """奖励"""
    resource: Resource
    count: int


class ArkSignResponse(BaseModel):
    """明日方舟签到响应"""
    awards: list[Award]
