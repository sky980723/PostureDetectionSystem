"""
弹窗提醒模块

生成弹窗消息内容，包含坐姿问题描述和改进建议。
"""

from typing import Dict, List, Any
from config.alert_config import AlertConfig


class PopupAlert:
    """
    弹窗提醒类

    生成结构化的弹窗消息内容，供前端显示。
    包含问题描述、改进建议和严重程度信息。
    """

    def __init__(self):
        """初始化弹窗提醒类"""
        pass

    def generate_message(self, posture_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成弹窗消息内容

        根据姿态状态生成包含问题描述和建议的弹窗消息。

        Args:
            posture_state: 姿态状态字典，包含:
                - status: str - 状态 ('good', 'warning', 'bad')
                - issues: List[str] - 问题类型列表
                - angles: Dict - 角度数据（可选）
                - timestamp: float - 时间戳（可选）

        Returns:
            Dict: 弹窗消息字典，包含:
                - title: str - 弹窗标题
                - severity: str - 严重程度
                - issues: List[Dict] - 问题列表，每项包含:
                    - type: str - 问题类型
                    - description: str - 问题描述
                - suggestions: List[str] - 改进建议列表
                - summary: str - 简要总结
        """
        status = posture_state.get('status', 'good')
        issues = posture_state.get('issues', [])
        angles = posture_state.get('angles', {})

        # 如果状态良好，返回空消息
        if status == 'good' or not issues:
            return {
                'title': AlertConfig.POPUP_TITLES.get('warning', '提醒'),
                'severity': 'good',
                'issues': [],
                'suggestions': [],
                'summary': '坐姿良好，请保持！'
            }

        # 构建问题列表
        issue_details = self._build_issue_details(issues, angles)

        # 收集所有建议
        all_suggestions = self._collect_suggestions(issues)

        # 生成总结
        summary = self._generate_summary(status, issues)

        return {
            'title': AlertConfig.POPUP_TITLES.get(status, '坐姿提醒'),
            'severity': status,
            'issues': issue_details,
            'suggestions': all_suggestions,
            'summary': summary
        }

    def _build_issue_details(
        self,
        issues: List[str],
        angles: Dict[str, float]
    ) -> List[Dict[str, str]]:
        """
        构建详细的问题信息列表

        Args:
            issues: 问题类型列表
            angles: 角度数据字典

        Returns:
            List[Dict]: 问题详情列表
        """
        issue_details = []

        for issue_type in issues:
            description = AlertConfig.get_issue_description(issue_type)

            # 如果有角度数据，添加到描述中
            if issue_type in angles:
                angle_value = angles[issue_type]
                description = f"{description}（{angle_value:.1f}°）"

            issue_details.append({
                'type': issue_type,
                'description': description
            })

        return issue_details

    def _collect_suggestions(self, issues: List[str]) -> List[str]:
        """
        收集所有问题对应的改进建议

        Args:
            issues: 问题类型列表

        Returns:
            List[str]: 去重后的建议列表
        """
        all_suggestions = []

        for issue_type in issues:
            suggestions = AlertConfig.get_issue_suggestions(issue_type)
            all_suggestions.extend(suggestions)

        # 去重但保持顺序
        unique_suggestions = []
        seen = set()

        for suggestion in all_suggestions:
            if suggestion not in seen:
                unique_suggestions.append(suggestion)
                seen.add(suggestion)

        return unique_suggestions

    def _generate_summary(self, status: str, issues: List[str]) -> str:
        """
        生成问题总结文本

        Args:
            status: 状态 ('warning', 'bad')
            issues: 问题类型列表

        Returns:
            str: 总结文本
        """
        issue_count = len(issues)

        if issue_count == 0:
            return "暂无坐姿问题"

        # 获取问题描述
        issue_names = [
            AlertConfig.get_issue_description(issue)
            for issue in issues
        ]

        if status == 'bad':
            prefix = "检测到严重坐姿问题："
        else:
            prefix = "检测到以下坐姿问题："

        # 将问题列表拼接为字符串
        issue_text = "、".join(issue_names)

        return f"{prefix}{issue_text}。请及时调整！"

    def format_suggestions(self, issues: List[str]) -> str:
        """
        将建议列表格式化为字符串（用于简单展示）

        Args:
            issues: 问题类型列表

        Returns:
            str: 格式化的建议文本，每条建议占一行
        """
        suggestions = self._collect_suggestions(issues)

        if not suggestions:
            return "暂无改进建议"

        # 格式化为带序号的列表
        formatted = []
        for i, suggestion in enumerate(suggestions, 1):
            formatted.append(f"{i}. {suggestion}")

        return "\n".join(formatted)

    @staticmethod
    def create_custom_message(
        title: str,
        severity: str,
        issues: List[Dict[str, str]],
        suggestions: List[str],
        summary: str
    ) -> Dict[str, Any]:
        """
        创建自定义弹窗消息

        允许完全自定义消息内容，用于特殊场景。

        Args:
            title: 弹窗标题
            severity: 严重程度
            issues: 问题列表
            suggestions: 建议列表
            summary: 总结文本

        Returns:
            Dict: 自定义弹窗消息字典
        """
        return {
            'title': title,
            'severity': severity,
            'issues': issues,
            'suggestions': suggestions,
            'summary': summary
        }

    def get_quick_message(self, issue_type: str) -> str:
        """
        获取单个问题的快速提示消息

        用于需要简短提示的场景。

        Args:
            issue_type: 问题类型

        Returns:
            str: 快速提示消息
        """
        description = AlertConfig.get_issue_description(issue_type)
        suggestions = AlertConfig.get_issue_suggestions(issue_type)

        if not suggestions:
            return f"检测到{description}，请注意调整坐姿。"

        # 只返回第一条建议
        first_suggestion = suggestions[0]
        return f"检测到{description}，建议：{first_suggestion}"
