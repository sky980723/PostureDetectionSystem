"""
数据存储层使用示例

演示如何使用数据库模型和存储服务
"""

import asyncio
from datetime import datetime, timedelta

from src.models.database import init_db, close_db, get_session
from src.storage.record_service import RecordService


async def main():
    """主函数"""
    print("=================================")
    print("数据存储层使用示例")
    print("=================================\n")

    # 1. 初始化数据库
    print("1. 初始化数据库...")
    await init_db()
    print("   数据库初始化完成\n")

    # 2. 获取会话并创建服务
    async for session in get_session():
        service = RecordService(session)

        # 3. 创建记录
        print("2. 创建姿态记录...")
        record1 = await service.create_record(
            posture_type="head_forward",
            severity=0.8,
            duration_seconds=30.5,
        )
        print(f"   记录1: {record1}")

        record2 = await service.create_record(
            posture_type="hunchback",
            severity=0.6,
            duration_seconds=20.0,
        )
        print(f"   记录2: {record2}")

        record3 = await service.create_record(
            posture_type="crossed_legs",
            severity=0.7,
            duration_seconds=25.3,
        )
        print(f"   记录3: {record3}\n")

        # 4. 查询所有记录
        print("3. 查询所有记录...")
        all_records = await service.get_records()
        print(f"   共找到 {len(all_records)} 条记录\n")

        # 5. 按姿态类型查询
        print("4. 查询 'head_forward' 类型的记录...")
        head_forward_records = await service.get_records(
            posture_type="head_forward"
        )
        print(f"   找到 {len(head_forward_records)} 条记录\n")

        # 6. 获取统计信息
        print("5. 获取今日统计...")
        stats = await service.get_statistics(period="day")
        print(f"   总记录数: {stats['total_records']}")
        print(f"   姿态分布: {stats['posture_distribution']}")
        print(f"   平均严重程度: {stats['avg_severity']:.3f}")
        print(f"   总持续时间: {stats['total_duration']:.2f} 秒\n")

        # 7. 根据 ID 查询
        print("6. 根据 ID 查询记录...")
        record_by_id = await service.get_record_by_id(record1.id)
        if record_by_id:
            print(f"   找到记录: {record_by_id}")
            print(f"   转为字典: {record_by_id.to_dict()}\n")

        # 8. 演示验证功能
        print("7. 演示参数验证...")
        try:
            await service.create_record(
                posture_type="invalid_type",
                severity=0.5,
                duration_seconds=10.0,
            )
        except ValueError as e:
            print(f"   捕获到预期错误: {e}\n")

        break

    # 9. 关闭数据库
    print("8. 关闭数据库连接...")
    await close_db()
    print("   完成！\n")

    print("=================================")
    print("示例运行完成")
    print("=================================")


if __name__ == "__main__":
    asyncio.run(main())
