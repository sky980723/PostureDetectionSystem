"""
历史记录 REST API 路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from src.api.deps import get_db_session
from src.storage.record_service import RecordService
from src.api.schemas.records import (
    RecordQueryParams,
    RecordListResponse,
    RecordItem
)

router = APIRouter(prefix="/api/records", tags=["records"])


@router.get("", response_model=RecordListResponse)
async def get_records(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    posture_type: Optional[str] = Query(None, description="姿态类型过滤"),
    limit: int = Query(100, ge=1, le=1000, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    session: AsyncSession = Depends(get_db_session)
):
    """
    查询历史记录

    支持按时间范围、姿态类型过滤，支持分页

    Args:
        start_time: 开始时间
        end_time: 结束时间
        posture_type: 姿态类型 (head_forward/hunchback/crossed_legs)
        limit: 每页数量 (1-1000)
        offset: 偏移量
        session: 数据库会话

    Returns:
        RecordListResponse: 记录列表和分页信息
    """
    try:
        # 验证参数
        query_params = RecordQueryParams(
            start_time=start_time,
            end_time=end_time,
            posture_type=posture_type,
            limit=limit,
            offset=offset
        )

        # 查询记录
        service = RecordService(session)
        records = await service.get_records(
            start_time=query_params.start_time,
            end_time=query_params.end_time,
            posture_type=query_params.posture_type,
            limit=query_params.limit,
            offset=query_params.offset
        )

        # 转换为响应格式
        record_items = [
            RecordItem(
                id=record.id,
                timestamp=record.timestamp.isoformat(),
                posture_type=record.posture_type,
                severity=record.severity,
                duration_seconds=record.duration_seconds
            )
            for record in records
        ]

        # 计算总数（简化版本，实际应该有单独的 count 方法）
        # 这里我们假设 limit 为实际返回的数量
        total = len(record_items) + query_params.offset

        return RecordListResponse(
            records=record_items,
            total=total,
            page=query_params.offset // query_params.limit + 1,
            page_size=query_params.limit
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
