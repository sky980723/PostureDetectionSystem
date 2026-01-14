"""
统计数据相关的 Pydantic Schema
"""

from datetime import datetime
from typing import Dict, Literal
from pydantic import BaseModel, Field


class StatisticsQueryParams(BaseModel):
    """统计查询参数"""
    period: Literal["day", "week", "month"] = Field(
        default="day",
        description="统计周期"
    )
    end_time: datetime | None = Field(
        None,
        description="结束时间，默认为当前时间"
    )


class StatisticsResponse(BaseModel):
    """统计数据响应"""
    total_records: int = Field(..., description="总记录数")
    posture_distribution: Dict[str, int] = Field(..., description="姿态类型分布")
    avg_severity: float = Field(..., description="平均严重程度")
    total_duration: float = Field(..., description="总持续时间（秒）")
    period_start: str = Field(..., description="统计开始时间 (ISO8601)")
    period_end: str = Field(..., description="统计结束时间 (ISO8601)")
