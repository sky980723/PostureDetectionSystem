"""
数据模型与迁移测试
"""

import sqlite3

from src.models.database import get_migrations_dir


def test_migration_script_contains_delete_and_column():
    """测试迁移脚本包含清理与新增字段逻辑"""
    versions_dir = get_migrations_dir() / "versions"
    migration_files = sorted(versions_dir.glob("*_pose_landmarks_field.py"))

    assert migration_files, "未找到 pose_landmarks 迁移脚本"

    migration_text = migration_files[-1].read_text(encoding="utf-8")
    assert "DELETE FROM posture_records" in migration_text
    assert "pose_landmarks" in migration_text


def test_migration_sql_clears_history_and_adds_column():
    """测试迁移 SQL 能清空历史并新增字段"""
    connection = sqlite3.connect(":memory:")
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE posture_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            posture_type TEXT NOT NULL,
            severity REAL NOT NULL,
            duration_seconds REAL NOT NULL
        )
        """
    )
    cursor.execute(
        """
        INSERT INTO posture_records (timestamp, posture_type, severity, duration_seconds)
        VALUES ('2024-01-01T00:00:00', 'head_forward', 0.5, 10.0)
        """
    )
    connection.commit()

    cursor.execute("DELETE FROM posture_records")
    cursor.execute("ALTER TABLE posture_records ADD COLUMN pose_landmarks TEXT")
    connection.commit()

    cursor.execute("SELECT COUNT(*) FROM posture_records")
    assert cursor.fetchone()[0] == 0

    cursor.execute("PRAGMA table_info(posture_records)")
    columns = {row[1] for row in cursor.fetchall()}
    assert "pose_landmarks" in columns

    connection.close()
