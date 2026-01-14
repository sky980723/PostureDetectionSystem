"""
设置管理 REST API 路由
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from src.api.schemas.settings import (
    SettingsResponse,
    SettingsUpdateRequest,
    SettingsUpdateResponse,
    AlertSettings,
    DetectionThresholds
)
from config.api_settings import api_settings
from config.settings import settings as detection_settings

router = APIRouter(prefix="/api/settings", tags=["settings"])

# 内存中存储当前设置（简化版本，生产环境应该使用数据库）
_current_settings = {
    "alert_settings": {
        "cooldown_seconds": api_settings.default_cooldown_seconds,
        "enable_sound": api_settings.default_enable_sound,
        "enable_popup": api_settings.default_enable_popup
    },
    "detection_thresholds": {
        "head_forward_angle": detection_settings.head_forward_angle_threshold,
        "hunchback_offset": detection_settings.hunchback_offset_threshold,
        "crossed_legs_diff": detection_settings.crossed_legs_x_diff_threshold
    }
}


@router.get("", response_model=SettingsResponse)
async def get_settings():
    """
    获取当前设置

    Returns:
        SettingsResponse: 当前提醒和检测设置
    """
    try:
        return SettingsResponse(
            alert_settings=AlertSettings(**_current_settings["alert_settings"]),
            detection_thresholds=DetectionThresholds(**_current_settings["detection_thresholds"])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get settings: {str(e)}")


@router.put("", response_model=SettingsUpdateResponse)
async def update_settings(request: SettingsUpdateRequest):
    """
    更新设置

    Args:
        request: 设置更新请求

    Returns:
        SettingsUpdateResponse: 更新结果和新的设置
    """
    try:
        updated_fields = []

        # 更新提醒设置
        if request.alert_settings is not None:
            _current_settings["alert_settings"].update(
                request.alert_settings.model_dump()
            )
            updated_fields.append("alert_settings")

        # 更新检测阈值
        if request.detection_thresholds is not None:
            _current_settings["detection_thresholds"].update(
                request.detection_thresholds.model_dump()
            )
            updated_fields.append("detection_thresholds")

            # 同步更新到 detection_settings（影响全局检测行为）
            if request.detection_thresholds.head_forward_angle is not None:
                detection_settings.head_forward_angle_threshold = request.detection_thresholds.head_forward_angle
            if request.detection_thresholds.hunchback_offset is not None:
                detection_settings.hunchback_offset_threshold = request.detection_thresholds.hunchback_offset
            if request.detection_thresholds.crossed_legs_diff is not None:
                detection_settings.crossed_legs_x_diff_threshold = request.detection_thresholds.crossed_legs_diff

        # 返回更新后的设置
        current = SettingsResponse(
            alert_settings=AlertSettings(**_current_settings["alert_settings"]),
            detection_thresholds=DetectionThresholds(**_current_settings["detection_thresholds"])
        )

        message = f"Successfully updated: {', '.join(updated_fields)}"

        return SettingsUpdateResponse(
            success=True,
            message=message,
            settings=current
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")


@router.post("/reset", response_model=SettingsResponse)
async def reset_settings():
    """
    重置所有设置到默认值

    Returns:
        SettingsResponse: 重置后的设置
    """
    try:
        # 重置为默认值
        _current_settings["alert_settings"] = {
            "cooldown_seconds": api_settings.default_cooldown_seconds,
            "enable_sound": api_settings.default_enable_sound,
            "enable_popup": api_settings.default_enable_popup
        }
        _current_settings["detection_thresholds"] = {
            "head_forward_angle": api_settings.default_head_forward_angle,
            "hunchback_offset": api_settings.default_hunchback_offset,
            "crossed_legs_diff": api_settings.default_crossed_legs_diff
        }

        return SettingsResponse(
            alert_settings=AlertSettings(**_current_settings["alert_settings"]),
            detection_thresholds=DetectionThresholds(**_current_settings["detection_thresholds"])
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset settings: {str(e)}")
