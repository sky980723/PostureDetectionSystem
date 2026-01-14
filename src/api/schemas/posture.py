"""
姿态检测相关的 Pydantic Schema

定义 WebSocket 通信的请求和响应数据结构
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator


class LandmarkSchema(BaseModel):
    """单个关键点的数据结构"""
    x: float = Field(..., description="X 坐标 (归一化, 0-1)")
    y: float = Field(..., description="Y 坐标 (归一化, 0-1)")
    z: float = Field(..., description="Z 坐标 (深度信息)")
    visibility: float = Field(..., ge=0.0, le=1.0, description="可见度 (0-1)")


class VideoFrameRequest(BaseModel):
    """客户端发送的视频帧请求"""
    type: str = Field(default="video_frame", description="消息类型")
    data: str = Field(..., description="Base64 编码的图像数据")
    timestamp: float = Field(..., description="客户端时间戳")
    frame_number: Optional[int] = Field(None, description="帧编号")

    @field_validator('data')
    @classmethod
    def validate_base64(cls, v):
        """验证 base64 数据格式"""
        if not v or len(v) < 10:
            raise ValueError("Invalid base64 image data")

        # 允许两种格式：
        # 1. 完整的 Data URL: data:image/jpeg;base64,/9j/4AAQ...
        # 2. 纯 base64 数据: /9j/4AAQ...
        # 前端发送的是纯 base64（已移除前缀），这样可以减少传输量

        # 如果是纯 base64，无需额外验证
        # 如果有前缀，确保格式正确
        if v.startswith('data:'):
            if not v.startswith('data:image/'):
                raise ValueError("Image data URL must start with 'data:image/'")

        return v


class AnalysisResult(BaseModel):
    """姿态分析结果"""
    head_forward: bool = Field(..., description="是否头部前倾")
    head_forward_angle: Optional[float] = Field(None, description="头部前倾角度")
    hunchback: bool = Field(..., description="是否驼背")
    hunchback_offset: Optional[float] = Field(None, description="驼背偏移量")
    crossed_legs: bool = Field(..., description="是否跷二郎腿")
    crossed_legs_diff: Optional[float] = Field(None, description="腿部偏移差异")
    valid: bool = Field(..., description="分析结果是否有效")


class AlertData(BaseModel):
    """提醒数据"""
    should_alert: bool = Field(..., description="是否应该触发提醒")
    sound_alert: Optional[Dict[str, Any]] = Field(None, description="声音提醒参数")
    popup_alert: Optional[Dict[str, Any]] = Field(None, description="弹窗提醒内容")


class StatusIndicator(BaseModel):
    """状态指示器数据"""
    status: str = Field(..., description="状态: good/warning/bad")
    color: str = Field(..., description="颜色代码")
    label: str = Field(..., description="状态标签")


class PostureResponse(BaseModel):
    """服务器返回的姿态检测结果"""
    type: str = Field(default="posture_result", description="消息类型")
    timestamp: str = Field(..., description="服务器时间戳 (ISO8601)")
    detected: bool = Field(..., description="是否检测到人体")
    pose_landmarks: Optional[List[LandmarkSchema]] = Field(None, description="33个关键点")
    analysis: Optional[AnalysisResult] = Field(None, description="姿态分析结果")
    alert: Optional[AlertData] = Field(None, description="提醒数据")
    status_indicator: Optional[StatusIndicator] = Field(None, description="状态指示器")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="检测置信度")


class ErrorResponse(BaseModel):
    """错误响应"""
    type: str = Field(default="error", description="消息类型")
    message: str = Field(..., description="错误消息")
    code: str = Field(..., description="错误代码")
    timestamp: str = Field(..., description="时间戳")


class PostureState(BaseModel):
    """姿态状态（用于 AlertManager）"""
    status: str = Field(..., description="状态: good/warning/bad")
    issues: List[str] = Field(default_factory=list, description="问题列表")
    angles: Dict[str, float] = Field(default_factory=dict, description="角度数据")
    timestamp: float = Field(..., description="时间戳")
