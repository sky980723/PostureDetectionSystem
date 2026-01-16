"""
WebSocket 姿态检测流处理

处理实时视频帧并返回姿态检测结果
"""

import base64
import asyncio
from datetime import datetime
from io import BytesIO
from typing import Optional
import numpy as np
from PIL import Image

from fastapi import WebSocket, WebSocketDisconnect
from src.detectors.pose_detector import PoseDetector, PoseResult
from src.analyzers.posture_analyzer import PostureAnalyzer
from src.alerts.alert_manager import AlertManager
from src.api.schemas.posture import (
    VideoFrameRequest,
    PostureResponse,
    ErrorResponse,
    LandmarkSchema,
    AnalysisResult,
    AlertData,
    StatusIndicator,
    PostureState
)
from config.api_settings import api_settings
import logging

logger = logging.getLogger(__name__)


class PostureStreamHandler:
    """
    姿态检测流处理器

    管理 WebSocket 连接，处理视频帧，返回检测结果
    """

    def __init__(
        self,
        websocket: WebSocket,
        pose_detector: PoseDetector,
        posture_analyzer: PostureAnalyzer,
        alert_manager: AlertManager,
        record_service=None
    ):
        """
        初始化处理器

        Args:
            websocket: WebSocket 连接
            pose_detector: 姿态检测器
            posture_analyzer: 坐姿分析器
            alert_manager: 提醒管理器
            record_service: 记录服务（可选）
        """
        self.websocket = websocket
        self.pose_detector = pose_detector
        self.posture_analyzer = posture_analyzer
        self.alert_manager = alert_manager
        self.record_service = record_service
        self.is_connected = False
        self.frame_count = 0
        self.last_process_time = 0.0
        self.min_frame_interval = 1.0 / api_settings.ws_frame_rate_limit  # 限流

    async def handle_connection(self):
        """
        处理 WebSocket 连接的主循环

        接收视频帧，处理并返回结果
        """
        await self.websocket.accept()
        self.is_connected = True
        logger.info("WebSocket connection established")

        try:
            while self.is_connected:
                # 接收消息
                try:
                    data = await asyncio.wait_for(
                        self.websocket.receive_json(),
                        timeout=api_settings.ws_heartbeat_interval
                    )
                except asyncio.TimeoutError:
                    # 心跳超时，发送 ping
                    await self.websocket.send_json({"type": "ping"})
                    continue

                # 处理消息
                try:
                    # 验证消息格式
                    frame_request = VideoFrameRequest(**data)

                    # 限流检查
                    current_time = asyncio.get_event_loop().time()
                    if current_time - self.last_process_time < self.min_frame_interval:
                        # 跳过此帧（限流）
                        continue
                    self.last_process_time = current_time

                    # 处理视频帧
                    response = await self.process_frame(frame_request)

                    # 发送响应
                    await self.websocket.send_json(response.model_dump())
                    self.frame_count += 1

                except ValueError as e:
                    # 数据验证错误
                    error_response = self._create_error_response(
                        f"Invalid frame data: {str(e)}",
                        "VALIDATION_ERROR"
                    )
                    await self.websocket.send_json(error_response.model_dump())

                except Exception as e:
                    # 处理错误
                    logger.error(f"Error processing frame: {e}", exc_info=True)
                    error_response = self._create_error_response(
                        f"Processing error: {str(e)}",
                        "PROCESSING_ERROR"
                    )
                    await self.websocket.send_json(error_response.model_dump())

        except WebSocketDisconnect:
            logger.info("WebSocket disconnected by client")
        except Exception as e:
            logger.error(f"WebSocket error: {e}", exc_info=True)
        finally:
            self.is_connected = False
            logger.info(f"WebSocket connection closed. Processed {self.frame_count} frames")

    async def process_frame(self, frame_request: VideoFrameRequest) -> PostureResponse:
        """
        处理单帧视频数据

        Args:
            frame_request: 视频帧请求

        Returns:
            PostureResponse: 检测结果
        """
        # 解码 base64 图像
        image = self._decode_base64_image(frame_request.data)

        # 姿态检测
        pose_result = self.pose_detector.detect(image)

        if not pose_result.detected:
            # 未检测到人体
            return PostureResponse(
                timestamp=datetime.now().isoformat(),
                detected=False,
                pose_landmarks=None,
                analysis=None,
                alert=None,
                status_indicator=StatusIndicator(
                    status="unknown",
                    color="gray",
                    label="未检测到"
                ),
                confidence=0.0
            )

        # 坐姿分析
        analysis_result = self.posture_analyzer.analyze(pose_result)

        # 转换 landmarks 为 schema
        landmarks = [
            LandmarkSchema(
                x=lm.x,
                y=lm.y,
                z=lm.z,
                visibility=lm.visibility
            )
            for lm in pose_result.landmarks
        ]

        # 构建姿态状态（用于提醒系统）
        posture_state = self._build_posture_state(analysis_result)

        # 检查是否需要提醒
        alert_result = self.alert_manager.check_and_alert(posture_state)

        # 如果触发告警，保存记录到数据库
        if alert_result['should_alert'] and self.record_service:
            try:
                # 获取最严重的问题类型作为主要姿态类型
                posture_type = posture_state['issues'][0] if posture_state['issues'] else "unknown"

                # 计算持续时间（假设每次告警间隔30秒的冷却时间）
                duration = 30.0

                # 计算严重程度（基于问题数量和状态）
                severity = 0.5 if posture_state['status'] == 'warning' else 0.8

                await self.record_service.create_record(
                    posture_type=posture_type,
                    severity=severity,
                    duration_seconds=duration,
                    timestamp=datetime.now()
                )
                logger.info(f"Alert record saved: {posture_type}, severity={severity}")
            except Exception as e:
                logger.error(f"Failed to save alert record: {e}", exc_info=True)

        # 构建分析结果（合并基础字段和前端需要的字段）
        analysis_dict = analysis_result.to_dict()
        analysis_dict.update({
            'status': posture_state['status'],
            'issues': posture_state['issues'],
            'angles': posture_state['angles']
        })

        # 构建响应
        return PostureResponse(
            timestamp=datetime.now().isoformat(),
            detected=True,
            pose_landmarks=landmarks,
            analysis=AnalysisResult(**analysis_dict),
            alert=AlertData(
                should_alert=alert_result['should_alert'],
                sound_alert=alert_result.get('sound_alert'),
                popup_alert=alert_result.get('popup_alert')
            ) if alert_result['should_alert'] else None,
            status_indicator=StatusIndicator(**alert_result['status_indicator']),
            confidence=self._calculate_confidence(pose_result)
        )

    def _decode_base64_image(self, base64_data: str) -> np.ndarray:
        """
        解码 base64 图像为 numpy array

        Args:
            base64_data: Base64 编码的图像（格式：data:image/jpeg;base64,xxx）

        Returns:
            numpy array (BGR 格式)
        """
        try:
            # 移除 data URL 前缀
            if ',' in base64_data:
                base64_data = base64_data.split(',')[1]

            # 解码 base64
            image_bytes = base64.b64decode(base64_data)

            # 使用 PIL 打开图像
            image = Image.open(BytesIO(image_bytes))

            # 转换为 RGB（模型推理需要 RGB）
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # 转换为 numpy array
            image_np = np.array(image)

            return image_np

        except Exception as e:
            raise ValueError(f"Failed to decode image: {e}")

    def _build_posture_state(self, analysis_result) -> dict:
        """
        构建姿态状态字典（用于 AlertManager）

        Args:
            analysis_result: PostureAnalysisResult

        Returns:
            姿态状态字典
        """
        issues = []
        angles = {}

        if analysis_result.head_forward:
            issues.append("head_forward")
            if analysis_result.head_forward_angle:
                angles["head_forward"] = analysis_result.head_forward_angle

        if analysis_result.hunchback:
            issues.append("hunchback")
            if analysis_result.hunchback_offset:
                angles["hunchback"] = analysis_result.hunchback_offset

        if analysis_result.crossed_legs:
            issues.append("crossed_legs")
            if analysis_result.crossed_legs_diff:
                angles["crossed_legs"] = analysis_result.crossed_legs_diff

        # 确定状态
        if not issues:
            status = "good"
        elif len(issues) >= 2:
            status = "bad"
        else:
            status = "warning"

        return {
            "status": status,
            "issues": issues,
            "angles": angles,
            "timestamp": asyncio.get_event_loop().time()
        }

    def _calculate_confidence(self, pose_result: PoseResult) -> float:
        """
        计算检测置信度（基于关键点可见度）

        Args:
            pose_result: 姿态检测结果

        Returns:
            置信度 (0-1)
        """
        visible_scores = [
            lm.visibility for lm in pose_result.landmarks
            if lm.visibility > 0.0
        ]
        if not visible_scores:
            return 0.0
        return sum(visible_scores) / len(visible_scores)

    def _create_error_response(self, message: str, code: str) -> ErrorResponse:
        """
        创建错误响应

        Args:
            message: 错误消息
            code: 错误代码

        Returns:
            ErrorResponse
        """
        return ErrorResponse(
            message=message,
            code=code,
            timestamp=datetime.now().isoformat()
        )


# ============================================================================
# WebSocket 端点处理函数
# ============================================================================

async def handle_posture_websocket(
    websocket: WebSocket,
    pose_detector: PoseDetector,
    posture_analyzer: PostureAnalyzer,
    alert_manager: AlertManager,
    record_service=None
):
    """
    WebSocket 端点处理函数

    Args:
        websocket: WebSocket 连接
        pose_detector: 姿态检测器
        posture_analyzer: 坐姿分析器
        alert_manager: 提醒管理器
        record_service: 记录服务（可选）
    """
    handler = PostureStreamHandler(
        websocket=websocket,
        pose_detector=pose_detector,
        posture_analyzer=posture_analyzer,
        alert_manager=alert_manager,
        record_service=record_service
    )
    await handler.handle_connection()
