"""
设置相关的 Pydantic Schema
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, model_validator


class AlertSettings(BaseModel):
    """提醒设置"""
    cooldown_seconds: float = Field(
        default=30.0,
        ge=5.0,
        le=300.0,
        description="冷却时间（秒）"
    )
    enable_sound: bool = Field(default=True, description="启用声音提醒")
    enable_popup: bool = Field(default=True, description="启用弹窗提醒")


class DetectionThresholds(BaseModel):
    """检测阈值设置"""
    head_forward_angle: float = Field(
        default=15.0,
        ge=5.0,
        le=45.0,
        description="头部前倾角度阈值（度）"
    )
    hunchback_offset: float = Field(
        default=0.1,
        ge=0.05,
        le=0.3,
        description="驼背偏移阈值"
    )
    crossed_legs_diff: float = Field(
        default=0.05,
        ge=0.02,
        le=0.2,
        description="跷二郎腿差异阈值"
    )


class SettingsResponse(BaseModel):
    """设置响应"""
    alert_settings: AlertSettings
    detection_thresholds: DetectionThresholds


class SettingsUpdateRequest(BaseModel):
    """设置更新请求"""
    alert_settings: Optional[AlertSettings] = None
    detection_thresholds: Optional[DetectionThresholds] = None

    @model_validator(mode='after')
    def at_least_one_field(self):
        """至少需要更新一个字段"""
        if self.alert_settings is None and self.detection_thresholds is None:
            raise ValueError("At least one settings field must be provided")
        return self


class SettingsUpdateResponse(BaseModel):
    """设置更新响应"""
    success: bool
    message: str
    settings: SettingsResponse
