"""
历史记录相关的 Pydantic Schema
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator


class RecordQueryParams(BaseModel):
    """历史记录查询参数"""
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    posture_type: Optional[str] = Field(None, description="姿态类型过滤")
    limit: int = Field(100, ge=1, le=1000, description="每页数量")
    offset: int = Field(0, ge=0, description="偏移量")

    @field_validator('posture_type')
    @classmethod
    def validate_posture_type(cls, v):
        """验证姿态类型"""
        if v is not None:
            valid_types = {"head_forward", "hunchback", "crossed_legs"}
            if v not in valid_types:
                raise ValueError(f"posture_type must be one of {valid_types}")
        return v

    @model_validator(mode='after')
    def validate_time_range(self):
        """验证时间范围"""
        if self.end_time is not None and self.start_time is not None:
            if self.end_time < self.start_time:
                raise ValueError("end_time must be after start_time")
        return self


class RecordItem(BaseModel):
    """单条记录"""
    id: int
    timestamp: str = Field(..., description="记录时间 (ISO8601)")
    posture_type: str
    severity: float
    duration_seconds: float

    class Config:
        from_attributes = True


class RecordListResponse(BaseModel):
    """记录列表响应"""
    records: List[RecordItem]
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
