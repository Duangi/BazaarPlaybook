import os
from typing import Optional, Tuple
from loguru import logger

try:
    from Quartz import (
        CGWindowListCopyWindowInfo,
        kCGWindowListOptionOnScreenOnly,
        kCGNullWindowID,
        CGEventGetLocation,
        CGEventCreate,
        kCGEventMouseMoved,
    )
    from AppKit import NSWorkspace
    QUARTZ_AVAILABLE = True
except ImportError:
    QUARTZ_AVAILABLE = False
    logger.warning("Quartz/AppKit not available - window management disabled on macOS")

from platforms.interfaces.window import WindowManager


class MacOSWindowManager(WindowManager):
    """macOS 平台窗口管理器实现（使用 Quartz 和 AppKit）"""
    
    def __init__(self):
        if not QUARTZ_AVAILABLE:
            logger.error("macOS window manager requires pyobjc-framework-Quartz and pyobjc-framework-Cocoa")
    
    def is_focus_valid(self, game_title: str = "The Bazaar") -> bool:
        """
        检查前台应用是否为游戏或本应用
        """
        if not QUARTZ_AVAILABLE:
            return False
            
        try:
            workspace = NSWorkspace.sharedWorkspace()
            active_app = workspace.frontmostApplication()
            
            if not active_app:
                return False
            
            # 1. 检查是否为游戏
            app_name = active_app.localizedName()
            if app_name and game_title.lower() in app_name.lower():
                return True
            
            # 2. 检查是否为本应用（通过 PID）
            active_pid = active_app.processIdentifier()
            if active_pid == os.getpid():
                return True
            
            return False
        except Exception as e:
            logger.error(f"is_focus_valid error: {e}")
            return False
    
    def get_window_rect(self, window_title: str, exact_match: bool = False) -> Optional[Tuple[int, int, int, int]]:
        """
        获取指定标题窗口的矩形区域
        
        注意：macOS 的窗口坐标系原点在左下角，需要转换为左上角坐标系
        """
        if not QUARTZ_AVAILABLE:
            return None
            
        try:
            # 获取所有可见窗口
            window_list = CGWindowListCopyWindowInfo(
                kCGWindowListOptionOnScreenOnly,
                kCGNullWindowID
            )
            
            for window in window_list:
                # 获取窗口标题
                title = window.get('kCGWindowName', '')
                owner_name = window.get('kCGWindowOwnerName', '')
                
                # 匹配窗口标题
                match = False
                if exact_match:
                    match = (title == window_title or owner_name == window_title)
                else:
                    match = (window_title.lower() in title.lower() or 
                            window_title.lower() in owner_name.lower())
                
                if match:
                    bounds = window.get('kCGWindowBounds', {})
                    x = int(bounds.get('X', 0))
                    y = int(bounds.get('Y', 0))
                    w = int(bounds.get('Width', 0))
                    h = int(bounds.get('Height', 0))
                    
                    # macOS 坐标系转换：Quartz 使用底部为原点，我们需要顶部为原点
                    # 这里返回的 y 已经是屏幕坐标系（顶部为原点），所以直接返回
                    return (x, y, w, h)
            
            return None
        except Exception as e:
            logger.error(f"get_window_rect error: {e}")
            return None
    
    def get_mouse_pos_relative(self, window_x: int, window_y: int) -> Tuple[int, int]:
        """
        获取相对于窗口的鼠标位置
        """
        if not QUARTZ_AVAILABLE:
            return (0, 0)
            
        try:
            # 创建一个鼠标移动事件以获取当前鼠标位置
            event = CGEventCreate(None)
            if event:
                loc = CGEventGetLocation(event)
                return (int(loc.x - window_x), int(loc.y - window_y))
            return (0, 0)
        except Exception as e:
            logger.error(f"get_mouse_pos_relative error: {e}")
            return (0, 0)
    
    def is_window_foreground(self, window_title: str) -> bool:
        """
        检查指定窗口是否在前台
        """
        if not QUARTZ_AVAILABLE:
            return False
            
        try:
            workspace = NSWorkspace.sharedWorkspace()
            active_app = workspace.frontmostApplication()
            
            if not active_app:
                return False
            
            app_name = active_app.localizedName()
            return app_name and window_title.lower() in app_name.lower()
        except Exception as e:
            logger.error(f"is_window_foreground error: {e}")
            return False
    
    def get_foreground_window_title(self) -> str:
        """
        获取前台窗口标题
        """
        if not QUARTZ_AVAILABLE:
            return ""
            
        try:
            workspace = NSWorkspace.sharedWorkspace()
            active_app = workspace.frontmostApplication()
            
            if not active_app:
                return ""
            
            return active_app.localizedName() or ""
        except Exception as e:
            logger.error(f"get_foreground_window_title error: {e}")
            return ""
    
    def restore_focus_to_game(self, game_title: str = "The Bazaar") -> bool:
        """
        恢复焦点到游戏窗口
        """
        if not QUARTZ_AVAILABLE:
            return False
            
        try:
            workspace = NSWorkspace.sharedWorkspace()
            running_apps = workspace.runningApplications()
            
            for app in running_apps:
                app_name = app.localizedName()
                if app_name and game_title.lower() in app_name.lower():
                    # 激活应用
                    success = app.activateWithOptions_(1 << 1)  # NSApplicationActivateIgnoringOtherApps
                    return bool(success)
            
            return False
        except Exception as e:
            logger.error(f"restore_focus_to_game error: {e}")
            return False
