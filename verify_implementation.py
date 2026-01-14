"""
测试验证脚本
用于验证核心检测引擎的实现
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, '/Users/sky/python_demo/PostureDetectionSystem')

def test_imports():
    """测试模块导入"""
    print("测试 1: 模块导入检查")
    print("-" * 50)

    try:
        from config.settings import settings, PostureDetectionSettings
        print("✓ 配置模块导入成功")

        from src.detectors.pose_detector import PoseDetector, PoseResult, Landmark
        print("✓ 检测器模块导入成功")

        from src.analyzers.posture_analyzer import PostureAnalyzer, PostureAnalysisResult
        print("✓ 分析器模块导入成功")

        print("\n所有模块导入成功!\n")
        return True
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False


def test_configuration():
    """测试配置"""
    print("测试 2: 配置验证")
    print("-" * 50)

    try:
        from config.settings import settings

        print(f"模型复杂度: {settings.model_complexity}")
        print(f"检测置信度: {settings.min_detection_confidence}")
        print(f"头部前倾阈值: {settings.head_forward_angle_threshold}°")
        print(f"驼背偏移阈值: {settings.hunchback_offset_threshold}")
        print(f"跷腿偏移阈值: {settings.crossed_legs_x_diff_threshold}")

        print("\n✓ 配置加载成功!\n")
        return True
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        return False


def test_detector_creation():
    """测试检测器创建"""
    print("测试 3: 检测器创建")
    print("-" * 50)

    try:
        from src.detectors.pose_detector import PoseDetector
        from unittest.mock import MagicMock, patch

        with patch('src.detectors.pose_detector.mp') as mock_mp:
            mock_pose_class = MagicMock()
            mock_pose_instance = MagicMock()
            mock_pose_class.return_value = mock_pose_instance
            mock_mp.solutions.pose.Pose = mock_pose_class

            detector = PoseDetector()
            print(f"✓ 检测器创建成功")
            print(f"  - 模型复杂度: {detector.model_complexity}")
            print(f"  - 检测置信度: {detector.min_detection_confidence}")

        print("\n✓ 检测器功能正常!\n")
        return True
    except Exception as e:
        print(f"✗ 检测器创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_analyzer_creation():
    """测试分析器创建"""
    print("测试 4: 分析器创建")
    print("-" * 50)

    try:
        from src.analyzers.posture_analyzer import PostureAnalyzer

        analyzer = PostureAnalyzer()
        print(f"✓ 分析器创建成功")
        print(f"  - 头部前倾阈值: {analyzer.head_forward_threshold}°")
        print(f"  - 驼背偏移阈值: {analyzer.hunchback_threshold}")
        print(f"  - 跷腿偏移阈值: {analyzer.crossed_legs_threshold}")

        print("\n✓ 分析器功能正常!\n")
        return True
    except Exception as e:
        print(f"✗ 分析器创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_structures():
    """测试数据结构"""
    print("测试 5: 数据结构验证")
    print("-" * 50)

    try:
        from src.detectors.pose_detector import Landmark, PoseResult
        from src.analyzers.posture_analyzer import PostureAnalysisResult

        # 测试 Landmark
        landmark = Landmark(x=0.5, y=0.5, z=0.0, visibility=0.9)
        assert landmark.x == 0.5
        print("✓ Landmark 数据类正常")

        # 测试 PoseResult
        landmarks = [landmark] * 33
        pose_result = PoseResult(landmarks=landmarks, detected=True)
        assert pose_result.detected is True
        assert len(pose_result.landmarks) == 33
        print("✓ PoseResult 数据类正常")

        # 测试 PostureAnalysisResult
        analysis = PostureAnalysisResult(
            head_forward=True,
            head_forward_angle=20.0,
            hunchback=False,
            hunchback_offset=0.15,
            crossed_legs=False,
            crossed_legs_diff=0.02,
            valid=True
        )
        assert analysis.head_forward is True
        print("✓ PostureAnalysisResult 数据类正常")

        print("\n✓ 所有数据结构正常!\n")
        return True
    except Exception as e:
        print(f"✗ 数据结构测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("=" * 50)
    print("核心检测引擎 - 功能验证")
    print("=" * 50)
    print()

    results = []
    results.append(("模块导入", test_imports()))
    results.append(("配置验证", test_configuration()))
    results.append(("检测器创建", test_detector_creation()))
    results.append(("分析器创建", test_analyzer_creation()))
    results.append(("数据结构", test_data_structures()))

    print("=" * 50)
    print("测试汇总")
    print("=" * 50)
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name:20s}: {status}")

    all_passed = all(r[1] for r in results)
    print()
    if all_passed:
        print("✓ 所有测试通过!")
        return 0
    else:
        print("✗ 部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
