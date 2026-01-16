"""
数据存储层单元测试

测试数据库模型和存储服务的功能
"""

import pytest
import json
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import init_db, close_db, get_session
from src.models.posture_record import PostureRecord
from src.storage.record_service import RecordService


@pytest.fixture
async def db_session():
    """
    提供测试用的内存数据库会话
    """
    # 使用内存 SQLite 数据库
    await init_db(db_path=":memory:", echo=False)

    # 获取会话
    async for session in get_session():
        yield session
        break

    # 清理
    await close_db()


@pytest.fixture
async def record_service(db_session: AsyncSession):
    """
    提供 RecordService 实例
    """
    return RecordService(db_session)


class TestPostureRecord:
    """测试 PostureRecord 模型"""

    def test_validate_posture_type(self):
        """测试姿态类型验证"""
        assert PostureRecord.validate_posture_type("head_forward") is True
        assert PostureRecord.validate_posture_type("hunchback") is True
        assert PostureRecord.validate_posture_type("crossed_legs") is True
        assert PostureRecord.validate_posture_type("invalid_type") is False
        assert PostureRecord.validate_posture_type("") is False

    def test_validate_severity(self):
        """测试严重程度验证"""
        assert PostureRecord.validate_severity(0.0) is True
        assert PostureRecord.validate_severity(0.5) is True
        assert PostureRecord.validate_severity(1.0) is True
        assert PostureRecord.validate_severity(-0.1) is False
        assert PostureRecord.validate_severity(1.1) is False

    def test_to_dict(self):
        """测试转换为字典"""
        timestamp = datetime(2024, 1, 15, 12, 0, 0)
        record = PostureRecord(
            id=1,
            timestamp=timestamp,
            posture_type="head_forward",
            severity=0.8,
            duration_seconds=30.5,
            pose_landmarks="[]",
        )

        result = record.to_dict()

        assert result["id"] == 1
        assert result["timestamp"] == "2024-01-15T12:00:00"
        assert result["posture_type"] == "head_forward"
        assert result["severity"] == 0.8
        assert result["duration_seconds"] == 30.5
        assert result["pose_landmarks"] == "[]"

    def test_repr(self):
        """测试字符串表示"""
        timestamp = datetime(2024, 1, 15, 12, 0, 0)
        record = PostureRecord(
            id=1,
            timestamp=timestamp,
            posture_type="hunchback",
            severity=0.75,
            duration_seconds=45.3,
        )

        repr_str = repr(record)

        assert "PostureRecord" in repr_str
        assert "id=1" in repr_str
        assert "hunchback" in repr_str
        assert "0.75" in repr_str
        assert "45.3s" in repr_str


class TestRecordService:
    """测试 RecordService 存储服务"""

    @pytest.mark.asyncio
    async def test_create_record_success(self, record_service: RecordService):
        """测试成功创建记录"""
        record = await record_service.create_record(
            posture_type="head_forward",
            severity=0.8,
            duration_seconds=30.5,
        )

        assert record.id is not None
        assert record.posture_type == "head_forward"
        assert record.severity == 0.8
        assert record.duration_seconds == 30.5
        assert record.timestamp is not None

    @pytest.mark.asyncio
    async def test_create_record_with_custom_timestamp(self, record_service: RecordService):
        """测试使用自定义时间创建记录"""
        custom_time = datetime(2024, 1, 15, 12, 0, 0)
        record = await record_service.create_record(
            posture_type="hunchback",
            severity=0.6,
            duration_seconds=20.0,
            timestamp=custom_time,
        )

        assert record.timestamp == custom_time

    @pytest.mark.asyncio
    async def test_create_record_with_pose_landmarks(self, record_service: RecordService):
        """测试保存关键点 JSON 数据"""
        pose_landmarks = [
            {"x": 0.1, "y": 0.2, "z": 0.0, "visibility": 0.9}
            for _ in range(17)
        ]
        record = await record_service.create_record(
            posture_type="head_forward",
            severity=0.4,
            duration_seconds=12.0,
            pose_landmarks=pose_landmarks,
        )

        assert record.pose_landmarks is not None
        decoded = json.loads(record.pose_landmarks)
        assert len(decoded) == 17
        assert decoded[0]["x"] == pytest.approx(0.1)

    @pytest.mark.asyncio
    async def test_create_record_with_pose_landmarks_string(self, record_service: RecordService):
        """测试使用 JSON 字符串保存关键点"""
        payload = json.dumps([{"x": 0.2, "y": 0.3, "z": 0.0, "visibility": 0.8}])
        record = await record_service.create_record(
            posture_type="hunchback",
            severity=0.5,
            duration_seconds=15.0,
            pose_landmarks=payload,
        )

        assert record.pose_landmarks == payload

    @pytest.mark.asyncio
    async def test_create_record_invalid_posture_type(self, record_service: RecordService):
        """测试使用无效姿态类型创建记录"""
        with pytest.raises(ValueError) as exc_info:
            await record_service.create_record(
                posture_type="invalid_type",
                severity=0.5,
                duration_seconds=10.0,
            )

        assert "Invalid posture_type" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_record_invalid_severity(self, record_service: RecordService):
        """测试使用无效严重程度创建记录"""
        with pytest.raises(ValueError) as exc_info:
            await record_service.create_record(
                posture_type="head_forward",
                severity=1.5,
                duration_seconds=10.0,
            )

        assert "Invalid severity" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_record_negative_duration(self, record_service: RecordService):
        """测试使用负数持续时间创建记录"""
        with pytest.raises(ValueError) as exc_info:
            await record_service.create_record(
                posture_type="head_forward",
                severity=0.5,
                duration_seconds=-10.0,
            )

        assert "Invalid duration_seconds" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_records_all(self, record_service: RecordService):
        """测试获取所有记录"""
        # 创建多条记录
        await record_service.create_record("head_forward", 0.8, 30.0)
        await record_service.create_record("hunchback", 0.6, 20.0)
        await record_service.create_record("crossed_legs", 0.7, 25.0)

        records = await record_service.get_records()

        assert len(records) == 3

    @pytest.mark.asyncio
    async def test_get_records_with_time_range(self, record_service: RecordService):
        """测试按时间范围查询记录"""
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        two_days_ago = now - timedelta(days=2)

        # 创建不同时间的记录
        await record_service.create_record(
            "head_forward", 0.8, 30.0, timestamp=two_days_ago
        )
        await record_service.create_record(
            "hunchback", 0.6, 20.0, timestamp=yesterday
        )
        await record_service.create_record(
            "crossed_legs", 0.7, 25.0, timestamp=now
        )

        # 查询最近一天的记录
        records = await record_service.get_records(
            start_time=yesterday - timedelta(hours=1),
            end_time=now + timedelta(hours=1),
        )

        assert len(records) == 2

    @pytest.mark.asyncio
    async def test_get_records_with_posture_type_filter(self, record_service: RecordService):
        """测试按姿态类型过滤记录"""
        await record_service.create_record("head_forward", 0.8, 30.0)
        await record_service.create_record("head_forward", 0.6, 20.0)
        await record_service.create_record("hunchback", 0.7, 25.0)

        records = await record_service.get_records(posture_type="head_forward")

        assert len(records) == 2
        assert all(r.posture_type == "head_forward" for r in records)

    @pytest.mark.asyncio
    async def test_get_records_with_limit_and_offset(self, record_service: RecordService):
        """测试分页查询"""
        # 创建 5 条记录
        for i in range(5):
            await record_service.create_record("head_forward", 0.5 + i * 0.1, 10.0 + i)

        # 获取第 2-3 条记录
        records = await record_service.get_records(limit=2, offset=1)

        assert len(records) == 2

    @pytest.mark.asyncio
    async def test_get_record_by_id(self, record_service: RecordService):
        """测试根据 ID 获取记录"""
        created = await record_service.create_record("head_forward", 0.8, 30.0)

        record = await record_service.get_record_by_id(created.id)

        assert record is not None
        assert record.id == created.id
        assert record.posture_type == "head_forward"

    @pytest.mark.asyncio
    async def test_get_record_by_id_not_found(self, record_service: RecordService):
        """测试获取不存在的记录"""
        record = await record_service.get_record_by_id(999)

        assert record is None

    @pytest.mark.asyncio
    async def test_get_statistics_day(self, record_service: RecordService):
        """测试获取日统计"""
        now = datetime.now()

        # 创建最近 24 小时内的记录
        await record_service.create_record(
            "head_forward", 0.8, 30.0, timestamp=now - timedelta(hours=2)
        )
        await record_service.create_record(
            "hunchback", 0.6, 20.0, timestamp=now - timedelta(hours=1)
        )
        await record_service.create_record(
            "head_forward", 0.7, 25.0, timestamp=now
        )

        # 创建 2 天前的记录（不应被统计）
        await record_service.create_record(
            "crossed_legs", 0.5, 15.0, timestamp=now - timedelta(days=2)
        )

        stats = await record_service.get_statistics(period="day")

        assert stats["total_records"] == 3
        assert stats["posture_distribution"]["good"] == 0
        assert stats["posture_distribution"]["warning"] == 1
        assert stats["posture_distribution"]["bad"] == 2
        assert stats["avg_severity"] == pytest.approx((0.8 + 0.6 + 0.7) / 3, rel=0.01)
        assert stats["total_duration"] == pytest.approx(75.0, rel=0.01)

    @pytest.mark.asyncio
    async def test_get_statistics_week(self, record_service: RecordService):
        """测试获取周统计"""
        now = datetime.now()

        # 创建最近 7 天内的记录
        for i in range(7):
            await record_service.create_record(
                "head_forward",
                0.5,
                10.0,
                timestamp=now - timedelta(days=i),
            )

        # 创建 8 天前的记录（不应被统计）
        await record_service.create_record(
            "hunchback", 0.5, 10.0, timestamp=now - timedelta(days=8)
        )

        stats = await record_service.get_statistics(period="week")

        assert stats["total_records"] == 7

    @pytest.mark.asyncio
    async def test_get_statistics_month(self, record_service: RecordService):
        """测试获取月统计"""
        now = datetime.now()

        # 创建最近 30 天内的记录
        await record_service.create_record(
            "head_forward", 0.5, 10.0, timestamp=now - timedelta(days=15)
        )
        await record_service.create_record(
            "hunchback", 0.6, 20.0, timestamp=now - timedelta(days=20)
        )

        # 创建 31 天前的记录（不应被统计）
        await record_service.create_record(
            "crossed_legs", 0.7, 30.0, timestamp=now - timedelta(days=31)
        )

        stats = await record_service.get_statistics(period="month")

        assert stats["total_records"] == 2

    @pytest.mark.asyncio
    async def test_get_statistics_empty(self, record_service: RecordService):
        """测试空数据统计"""
        stats = await record_service.get_statistics(period="day")

        assert stats["total_records"] == 0
        assert stats["posture_distribution"] == {}
        assert stats["avg_severity"] == 0.0
        assert stats["total_duration"] == 0.0

    @pytest.mark.asyncio
    async def test_get_statistics_invalid_period(self, record_service: RecordService):
        """测试无效的统计周期"""
        with pytest.raises(ValueError) as exc_info:
            await record_service.get_statistics(period="invalid")

        assert "Invalid period" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_record(self, record_service: RecordService):
        """测试删除记录"""
        record = await record_service.create_record("head_forward", 0.8, 30.0)

        result = await record_service.delete_record(record.id)

        assert result is True

        # 验证已删除
        deleted = await record_service.get_record_by_id(record.id)
        assert deleted is None

    @pytest.mark.asyncio
    async def test_delete_record_not_found(self, record_service: RecordService):
        """测试删除不存在的记录"""
        result = await record_service.delete_record(999)

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_old_records(self, record_service: RecordService):
        """测试删除旧记录"""
        now = datetime.now()

        # 创建新记录（应保留）
        await record_service.create_record(
            "head_forward", 0.8, 30.0, timestamp=now - timedelta(days=30)
        )

        # 创建旧记录（应删除）
        await record_service.create_record(
            "hunchback", 0.6, 20.0, timestamp=now - timedelta(days=100)
        )
        await record_service.create_record(
            "crossed_legs", 0.7, 25.0, timestamp=now - timedelta(days=120)
        )

        # 删除 90 天前的记录
        deleted_count = await record_service.delete_old_records(days=90)

        assert deleted_count == 2

        # 验证剩余记录
        remaining = await record_service.get_records()
        assert len(remaining) == 1


class TestDatabaseIntegration:
    """测试数据库集成功能"""

    @pytest.mark.asyncio
    async def test_database_initialization(self):
        """测试数据库初始化"""
        engine = await init_db(db_path=":memory:")

        assert engine is not None

        # 验证可以获取会话
        async for session in get_session():
            assert session is not None
            break

        await close_db()

    @pytest.mark.asyncio
    async def test_session_without_initialization(self):
        """测试未初始化时获取会话"""
        await close_db()  # 确保已关闭

        with pytest.raises(RuntimeError) as exc_info:
            async for session in get_session():
                pass

        assert "not initialized" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_multiple_records_persistence(self, record_service: RecordService):
        """测试多条记录的持久化"""
        # 创建多条记录
        records_data = [
            ("head_forward", 0.8, 30.0),
            ("hunchback", 0.6, 20.0),
            ("crossed_legs", 0.7, 25.0),
        ]

        created_ids = []
        for posture_type, severity, duration in records_data:
            record = await record_service.create_record(
                posture_type, severity, duration
            )
            created_ids.append(record.id)

        # 验证所有记录都能被查询到
        for record_id in created_ids:
            record = await record_service.get_record_by_id(record_id)
            assert record is not None

    @pytest.mark.asyncio
    async def test_concurrent_record_creation(self):
        """测试并发创建记录（使用独立session避免冲突）"""
        import asyncio

        # 初始化测试数据库
        await init_db(db_path=":memory:", echo=False)

        try:
            async def create_one_record(i: int):
                """创建单条记录（使用独立session）"""
                async for session in get_session():
                    service = RecordService(session)
                    record = await service.create_record(
                        "head_forward",
                        0.5 + i * 0.1,
                        10.0 + i
                    )
                    return record

            # 并发创建多条记录（每个任务使用独立session）
            tasks = [create_one_record(i) for i in range(5)]
            records = await asyncio.gather(*tasks)

            assert len(records) == 5
            # 验证所有记录都有唯一 ID
            ids = [r.id for r in records]
            assert len(set(ids)) == 5
        finally:
            # 清理
            await close_db()
