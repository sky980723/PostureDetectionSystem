"""
记录存储服务

提供姿态记录的 CRUD 操作和统计查询功能
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.posture_record import PostureRecord

PeriodType = Literal["day", "week", "month"]


class RecordService:
    """
    姿态记录存储服务

    提供记录的创建、查询和统计功能
    """

    def __init__(self, session: AsyncSession):
        """
        初始化服务

        Args:
            session: 异步数据库会话
        """
        self.session = session

    async def create_record(
        self,
        posture_type: str,
        severity: float,
        duration_seconds: float,
        timestamp: datetime | None = None,
    ) -> PostureRecord:
        """
        创建新的姿态记录

        Args:
            posture_type: 姿态类型 (head_forward/hunchback/crossed_legs)
            severity: 严重程度 (0.0-1.0)
            duration_seconds: 持续时间（秒）
            timestamp: 记录时间，如果为 None 则使用当前时间

        Returns:
            创建的 PostureRecord 对象

        Raises:
            ValueError: 如果参数验证失败
        """
        # 验证参数
        if not PostureRecord.validate_posture_type(posture_type):
            raise ValueError(
                f"Invalid posture_type: {posture_type}. "
                f"Must be one of: head_forward, hunchback, crossed_legs"
            )

        if not PostureRecord.validate_severity(severity):
            raise ValueError(
                f"Invalid severity: {severity}. Must be between 0.0 and 1.0"
            )

        if duration_seconds < 0:
            raise ValueError(
                f"Invalid duration_seconds: {duration_seconds}. Must be non-negative"
            )

        # 创建记录
        record = PostureRecord(
            posture_type=posture_type,
            severity=severity,
            duration_seconds=duration_seconds,
        )

        if timestamp is not None:
            record.timestamp = timestamp

        # 保存到数据库
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)

        return record

    async def get_records(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        posture_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[PostureRecord]:
        """
        查询姿态记录

        Args:
            start_time: 起始时间（包含），如果为 None 则不限制
            end_time: 结束时间（包含），如果为 None 则不限制
            posture_type: 姿态类型过滤，如果为 None 则返回所有类型
            limit: 最大返回记录数
            offset: 偏移量（用于分页）

        Returns:
            PostureRecord 对象列表，按时间倒序排列
        """
        # 构建查询
        query = select(PostureRecord)

        # 添加时间范围过滤
        if start_time is not None:
            query = query.where(PostureRecord.timestamp >= start_time)
        if end_time is not None:
            query = query.where(PostureRecord.timestamp <= end_time)

        # 添加姿态类型过滤
        if posture_type is not None:
            query = query.where(PostureRecord.posture_type == posture_type)

        # 按时间倒序排列
        query = query.order_by(PostureRecord.timestamp.desc())

        # 添加分页
        query = query.limit(limit).offset(offset)

        # 执行查询
        result = await self.session.execute(query)
        records = result.scalars().all()

        return list(records)

    async def get_record_by_id(self, record_id: int) -> PostureRecord | None:
        """
        根据 ID 获取单条记录

        Args:
            record_id: 记录 ID

        Returns:
            PostureRecord 对象，如果不存在则返回 None
        """
        query = select(PostureRecord).where(PostureRecord.id == record_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_statistics(
        self,
        period: PeriodType = "day",
        end_time: datetime | None = None,
    ) -> Dict[str, Any]:
        """
        获取统计信息

        Args:
            period: 统计周期 ('day'=最近24小时, 'week'=最近7天, 'month'=最近30天)
            end_time: 统计结束时间，如果为 None 则使用当前时间

        Returns:
            统计信息字典，包含:
            - total_records: 总记录数
            - posture_distribution: 各姿态类型的记录数
            - avg_severity: 平均严重程度
            - total_duration: 总持续时间（秒）
            - period_start: 统计开始时间
            - period_end: 统计结束时间
        """
        if end_time is None:
            end_time = datetime.now()

        # 计算起始时间
        if period == "day":
            start_time = end_time - timedelta(days=1)
        elif period == "week":
            start_time = end_time - timedelta(weeks=1)
        elif period == "month":
            start_time = end_time - timedelta(days=30)
        else:
            raise ValueError(f"Invalid period: {period}. Must be 'day', 'week', or 'month'")

        # 查询指定时间范围内的所有记录
        records = await self.get_records(
            start_time=start_time,
            end_time=end_time,
            limit=10000,  # 设置一个较大的限制以获取所有记录
        )

        # 计算统计信息
        total_records = len(records)

        if total_records == 0:
            return {
                "total_records": 0,
                "posture_distribution": {},
                "avg_severity": 0.0,
                "total_duration": 0.0,
                "period_start": start_time.isoformat(),
                "period_end": end_time.isoformat(),
            }

        # 计算姿态分布和状态分布
        posture_distribution: Dict[str, int] = {}
        status_distribution: Dict[str, int] = {"good": 0, "warning": 0, "bad": 0}
        total_severity = 0.0
        total_duration = 0.0

        for record in records:
            # 统计姿态类型
            posture_distribution[record.posture_type] = (
                posture_distribution.get(record.posture_type, 0) + 1
            )

            # 根据严重程度映射到状态
            # 0.0-0.3: good, 0.3-0.7: warning, 0.7-1.0: bad
            if record.severity < 0.3:
                status_distribution["good"] += 1
            elif record.severity < 0.7:
                status_distribution["warning"] += 1
            else:
                status_distribution["bad"] += 1

            # 累加严重程度
            total_severity += record.severity
            # 累加持续时间
            total_duration += record.duration_seconds

        # 计算平均严重程度
        avg_severity = total_severity / total_records

        # 返回status分布而不是posture分布（匹配前端需求）
        return {
            "total_records": total_records,
            "posture_distribution": status_distribution,  # 前端需要按status统计
            "avg_severity": round(avg_severity, 3),
            "total_duration": round(total_duration, 2),
            "period_start": start_time.isoformat(),
            "period_end": end_time.isoformat(),
        }

    async def delete_record(self, record_id: int) -> bool:
        """
        删除指定记录

        Args:
            record_id: 记录 ID

        Returns:
            如果删除成功返回 True，记录不存在返回 False
        """
        record = await self.get_record_by_id(record_id)
        if record is None:
            return False

        await self.session.delete(record)
        await self.session.commit()
        return True

    async def delete_old_records(self, days: int = 90) -> int:
        """
        删除指定天数之前的旧记录

        Args:
            days: 保留最近多少天的记录

        Returns:
            删除的记录数
        """
        cutoff_time = datetime.now() - timedelta(days=days)

        # 查询需要删除的记录
        query = select(PostureRecord).where(PostureRecord.timestamp < cutoff_time)
        result = await self.session.execute(query)
        records = result.scalars().all()

        # 删除记录
        for record in records:
            await self.session.delete(record)

        await self.session.commit()
        return len(records)
