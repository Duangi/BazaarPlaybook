"""
窗口工具模块 - 跨平台适配器代理

此模块提供与平台无关的窗口管理函数，内部通过 PlatformAdapter 自动选择
对应平台的实现（Windows/macOS）。

主要功能：
- 焦点验证
- 窗口矩形获取
- 鼠标位置计算
- 窗口前台检测
- 焦点恢复

使用示例：
    from utils.window_utils import get_window_rect, restore_focus_to_game
    
    rect = get_window_rect("The Bazaar")
    if rect:
        x, y, w, h = rect
        print(f"Game window at {x},{y} size {w}x{h}")
"""

from typing import Optional, Tuple
from platforms.adapter import PlatformAdapter

# 获取平台特定的窗口管理器实例（单例模式）
_window_manager = None

def _get_manager():
    """懒加载窗口管理器"""
    global _window_manager
    if _window_manager is None:
        _window_manager = PlatformAdapter.get_window_manager()
    return _window_manager


def is_focus_valid(game_title: str = "The Bazaar") -> bool:
    """
    检查焦点窗口是否有效（游戏窗口或应用自身）
    
    Args:
        game_title: 游戏窗口标题，默认 "The Bazaar"
        
    Returns:
        bool: 焦点是否有效
    """
    return _get_manager().is_focus_valid(game_title)


def get_window_rect(window_title: str, exact_match: bool = False) -> Optional[Tuple[int, int, int, int]]:
    """
    获取窗口的客户区矩形
    
    Args:
        window_title: 窗口标题
        exact_match: 是否精确匹配标题（默认 False，允许模糊匹配）
        
    Returns:
        Optional[Tuple[int, int, int, int]]: (x, y, width, height) 或 None（未找到窗口）
    """
    return _get_manager().get_window_rect(window_title, exact_match)


def get_mouse_pos_relative(window_x: int, window_y: int) -> Tuple[int, int]:
    """
    获取相对于窗口的鼠标位置
    
    Args:
        window_x: 窗口左上角 X 坐标
        window_y: 窗口左上角 Y 坐标
        
    Returns:
        Tuple[int, int]: 相对于窗口的鼠标坐标 (x, y)
    """
    return _get_manager().get_mouse_pos_relative(window_x, window_y)


def is_window_foreground(window_title: str) -> bool:
    """
    检查指定标题的窗口是否在前台
    
    Args:
        window_title: 窗口标题
        
    Returns:
        bool: 是否在前台
    """
    return _get_manager().is_window_foreground(window_title)


def get_foreground_window_title() -> str:
    """
    获取前台窗口标题
    
    Returns:
        str: 窗口标题，如果无法获取则返回空字符串
    """
    return _get_manager().get_foreground_window_title()


def restore_focus_to_game(game_title: str = "The Bazaar") -> bool:
    """
    恢复焦点到游戏窗口
    
    Args:
        game_title: 游戏窗口标题，默认 "The Bazaar"
        
    Returns:
        bool: 是否成功恢复焦点
    """
    return _get_manager().restore_focus_to_game(game_title)

