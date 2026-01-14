"""
核心检测引擎使用示例

演示如何使用 PoseDetector 和 PostureAnalyzer 进行坐姿检测
"""

import numpy as np
import cv2
from src.detectors.pose_detector import PoseDetector
from src.analyzers.posture_analyzer import PostureAnalyzer


def example_basic_usage():
    """示例 1: 基础使用"""
    print("=" * 60)
    print("示例 1: 基础使用")
    print("=" * 60)

    # 创建检测器和分析器
    detector = PoseDetector()
    analyzer = PostureAnalyzer()

    # 创建测试图像 (实际使用中应从摄像头或文件读取)
    image = np.zeros((480, 640, 3), dtype=np.uint8)

    try:
        # 执行检测
        pose_result = detector.detect(image)

        if pose_result.detected:
            print("✓ 检测到人体")
            print(f"  关键点数量: {len(pose_result.landmarks)}")

            # 分析坐姿
            analysis = analyzer.analyze(pose_result)

            if analysis.valid:
                print("\n坐姿分析结果:")
                print(f"  头部前倾: {analysis.head_forward}")
                if analysis.head_forward_angle is not None:
                    print(f"    角度: {analysis.head_forward_angle:.1f}°")

                print(f"  驼背: {analysis.hunchback}")
                if analysis.hunchback_offset is not None:
                    print(f"    偏移: {analysis.hunchback_offset:.3f}")

                print(f"  跷二郎腿: {analysis.crossed_legs}")
                if analysis.crossed_legs_diff is not None:
                    print(f"    差异: {analysis.crossed_legs_diff:.3f}")
            else:
                print("⚠ 分析结果无效(关键点不可见)")
        else:
            print("✗ 未检测到人体")

    finally:
        detector.close()

    print()


def example_context_manager():
    """示例 2: 使用上下文管理器"""
    print("=" * 60)
    print("示例 2: 使用上下文管理器")
    print("=" * 60)

    image = np.zeros((480, 640, 3), dtype=np.uint8)

    # 使用 with 语句自动管理资源
    with PoseDetector() as detector:
        pose_result = detector.detect(image)
        print(f"检测结果: detected={pose_result.detected}")

    print("✓ 资源已自动释放\n")


def example_custom_configuration():
    """示例 3: 自定义配置"""
    print("=" * 60)
    print("示例 3: 自定义配置")
    print("=" * 60)

    # 自定义检测器配置
    detector = PoseDetector(
        model_complexity=2,  # 使用高精度模型
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    )

    # 自定义分析器配置
    analyzer = PostureAnalyzer(
        head_forward_threshold=20.0,  # 更宽松的阈值
        hunchback_threshold=0.15,
        crossed_legs_threshold=0.08
    )

    print(f"检测器配置:")
    print(f"  模型复杂度: {detector.model_complexity}")
    print(f"  检测置信度: {detector.min_detection_confidence}")

    print(f"\n分析器配置:")
    print(f"  头部前倾阈值: {analyzer.head_forward_threshold}°")
    print(f"  驼背偏移阈值: {analyzer.hunchback_threshold}")
    print(f"  跷腿偏移阈值: {analyzer.crossed_legs_threshold}")

    detector.close()
    print()


def example_landmark_access():
    """示例 4: 访问关键点"""
    print("=" * 60)
    print("示例 4: 访问关键点")
    print("=" * 60)

    # 创建模拟的检测结果
    from src.detectors.pose_detector import Landmark, PoseResult

    landmarks = []
    for i in range(33):
        landmarks.append(Landmark(
            x=0.5 + i * 0.01,
            y=0.5 + i * 0.01,
            z=0.0,
            visibility=0.9
        ))

    pose_result = PoseResult(landmarks=landmarks, detected=True)

    # 访问特定关键点
    nose = pose_result.get_landmark(PoseDetector.NOSE)
    if nose:
        print(f"鼻子位置: ({nose.x:.2f}, {nose.y:.2f})")

    left_shoulder = pose_result.get_landmark(PoseDetector.LEFT_SHOULDER)
    if left_shoulder:
        print(f"左肩位置: ({left_shoulder.x:.2f}, {left_shoulder.y:.2f})")

    # 检查可见性
    if pose_result.is_landmark_visible(PoseDetector.LEFT_EAR):
        print("✓ 左耳可见")

    # 使用自定义阈值检查可见性
    if pose_result.is_landmark_visible(PoseDetector.RIGHT_EAR, threshold=0.8):
        print("✓ 右耳可见(阈值 0.8)")

    print()


def example_result_serialization():
    """示例 5: 结果序列化"""
    print("=" * 60)
    print("示例 5: 结果序列化")
    print("=" * 60)

    from src.detectors.pose_detector import Landmark
    from src.analyzers.posture_analyzer import PostureAnalysisResult

    # 创建分析结果
    analysis = PostureAnalysisResult(
        head_forward=True,
        head_forward_angle=18.5,
        hunchback=False,
        hunchback_offset=0.12,
        crossed_legs=True,
        crossed_legs_diff=0.07,
        valid=True
    )

    # 转换为字典(可用于 JSON 序列化)
    result_dict = analysis.to_dict()

    print("分析结果(字典格式):")
    for key, value in result_dict.items():
        print(f"  {key}: {value}")

    # Landmark 也支持序列化
    landmark = Landmark(x=0.5, y=0.6, z=0.1, visibility=0.95)
    landmark_dict = landmark.to_dict()

    print("\n关键点(字典格式):")
    for key, value in landmark_dict.items():
        print(f"  {key}: {value}")

    print()


def example_error_handling():
    """示例 6: 错误处理"""
    print("=" * 60)
    print("示例 6: 错误处理")
    print("=" * 60)

    detector = PoseDetector()

    try:
        # 尝试传入无效输入
        print("测试 1: 传入列表而非 numpy 数组")
        detector.detect([1, 2, 3])
    except ValueError as e:
        print(f"✓ 捕获异常: {e}")

    try:
        # 尝试传入错误维度的图像
        print("\n测试 2: 传入单通道图像")
        invalid_image = np.zeros((480, 640), dtype=np.uint8)
        detector.detect(invalid_image)
    except ValueError as e:
        print(f"✓ 捕获异常: {e}")

    detector.close()
    print()


def example_video_stream():
    """示例 7: 视频流处理(伪代码)"""
    print("=" * 60)
    print("示例 7: 视频流处理(伪代码)")
    print("=" * 60)

    print("""
    # 实际使用中的视频流处理示例
    import cv2

    detector = PoseDetector()
    analyzer = PostureAnalyzer()

    # 打开摄像头
    cap = cv2.VideoCapture(0)

    try:
        while True:
            # 读取帧
            ret, frame = cap.read()
            if not ret:
                break

            # 检测和分析
            pose_result = detector.detect(frame)

            if pose_result.detected:
                analysis = analyzer.analyze(pose_result)

                if analysis.valid:
                    # 显示结果
                    if analysis.head_forward:
                        print("警告: 头部前倾!")
                    if analysis.hunchback:
                        print("警告: 驼背!")
                    if analysis.crossed_legs:
                        print("警告: 跷二郎腿!")

            # 显示画面
            cv2.imshow('Posture Detection', frame)

            # 按 q 退出
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        detector.close()
    """)
    print()


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("核心检测引擎使用示例")
    print("=" * 60 + "\n")

    # 运行所有示例
    example_basic_usage()
    example_context_manager()
    example_custom_configuration()
    example_landmark_access()
    example_result_serialization()
    example_error_handling()
    example_video_stream()

    print("=" * 60)
    print("所有示例运行完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
