#!/usr/bin/env python3
"""测试记录保存和统计功能"""

import asyncio
import sys
from datetime import datetime, timedelta
from sqlalchemy import text

from sqlalchemy.ext.asyncio import AsyncSession
from src.models.database import init_db, get_session
from src.storage.record_service import RecordService


async def test_record_save():
    """测试记录保存和统计"""
    print("初始化数据库...")
    await init_db()

    async for session in get_session():
        service = RecordService(session)

        # 清空现有记录（测试用）
        print("\n清空旧记录...")
        await session.execute(text("DELETE FROM posture_records"))
        await session.commit()

        # 创建测试记录
        print("\n创建测试记录...")
        records = [
            # warning级别记录 (severity=0.5)
            {"posture_type": "head_forward", "severity": 0.5, "duration_seconds": 30.0},
            {"posture_type": "hunchback", "severity": 0.5, "duration_seconds": 30.0},

            # bad级别记录 (severity=0.8)
            {"posture_type": "crossed_legs", "severity": 0.8, "duration_seconds": 30.0},
            {"posture_type": "head_forward", "severity": 0.8, "duration_seconds": 30.0},
            {"posture_type": "hunchback", "severity": 0.8, "duration_seconds": 30.0},
        ]

        for i, record_data in enumerate(records):
            # 创建记录，时间间隔1小时
            timestamp = datetime.now() - timedelta(hours=i)
            record = await service.create_record(
                **record_data,
                timestamp=timestamp
            )
            print(f"✓ 记录 {record.id}: {record.posture_type}, severity={record.severity}")

        # 查询统计
        print("\n查询本周统计...")
        stats = await service.get_statistics(period="week")

        print(f"\n统计结果:")
        print(f"总记录数: {stats['total_records']}")
        print(f"状态分布: {stats['posture_distribution']}")
        print(f"平均严重程度: {stats['avg_severity']}")
        print(f"总持续时间: {stats['total_duration']}秒")

        # 验证
        assert stats['total_records'] == 5, f"预期5条记录，实际{stats['total_records']}"
        assert stats['posture_distribution']['warning'] == 2, f"预期2条warning记录"
        assert stats['posture_distribution']['bad'] == 3, f"预期3条bad记录"
        assert stats['posture_distribution']['good'] == 0, f"预期0条good记录"

        print("\n✅ 所有测试通过！")
        print(f"\n数据库记录已创建，可以刷新浏览器查看前端统计效果")

        return stats


if __name__ == "__main__":
    try:
        asyncio.run(test_record_save())
    except Exception as e:
        print(f"❌ 测试失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
