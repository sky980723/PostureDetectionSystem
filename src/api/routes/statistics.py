"""
统计数据 REST API 路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Literal, Optional
from datetime import datetime

from src.api.deps import get_db_session
from src.storage.record_service import RecordService
from src.api.schemas.statistics import (
    StatisticsQueryParams,
    StatisticsResponse
)

router = APIRouter(prefix="/api/statistics", tags=["statistics"])


@router.get("", response_model=StatisticsResponse)
async def get_statistics(
    period: Literal["day", "week", "month"] = Query("day", description="统计周期"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    session: AsyncSession = Depends(get_db_session)
):
    """
    获取统计数据

    按日/周/月维度统计姿态记录

    Args:
        period: 统计周期 (day/week/month)
        end_time: 结束时间（默认为当前时间）
        session: 数据库会话

    Returns:
        StatisticsResponse: 统计数据
    """
    try:
        # 验证参数
        query_params = StatisticsQueryParams(
            period=period,
            end_time=end_time
        )

        # 查询统计数据
        service = RecordService(session)
        stats = await service.get_statistics(
            period=query_params.period,
            end_time=query_params.end_time
        )

        # 转换为响应格式
        return StatisticsResponse(
            total_records=stats['total_records'],
            posture_distribution=stats['posture_distribution'],
            avg_severity=stats['avg_severity'],
            total_duration=stats['total_duration'],
            period_start=stats['period_start'].isoformat(),
            period_end=stats['period_end'].isoformat()
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
