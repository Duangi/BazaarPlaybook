import os
from typing import Optional, Tuple
from loguru import logger

try:
    from Xlib import display, X
    import ewmh
    XLIB_AVAILABLE = True
except ImportError:
    XLIB_AVAILABLE = False
    logger.warning("Xlib/ewmh not available - window management disabled on Linux")

from platforms.interfaces.window import WindowManager


class LinuxWindowManager(WindowManager):
    """
    Linux 平台窗口管理器实现（支持 X11，包括 Steam Deck）
    
    使用 python-xlib 和 ewmh 库实现窗口管理功能。
    适用于大多数 Linux 桌面环境（GNOME, KDE, XFCE 等）和 Steam Deck。
    
    注意：Wayland 支持有限，建议在 X11 会话下运行。
    """
    
    def __init__(self):
        if not XLIB_AVAILABLE:
            logger.error("Linux window manager requires python-xlib and ewmh")
            self.display = None
            self.ewmh_obj = None
        else:
            try:
                self.display = display.Display()
                self.ewmh_obj = ewmh.EWMH()
            except Exception as e:
                logger.error(f"Failed to initialize X11 display: {e}")
                self.display = None
                self.ewmh_obj = None
    
    def _get_pid(self) -> int:
        """获取当前进程 PID"""
        return os.getpid()
    
    def _find_window_by_title(self, title: str, exact_match: bool = False) -> Optional[any]:
        """
        通过标题查找窗口
        
        Args:
            title: 窗口标题
            exact_match: 是否精确匹配
            
        Returns:
            窗口对象或 None
        """
        if not self.display or not self.ewmh_obj:
            return None
        
        try:
            # 获取所有客户端窗口
            windows = self.ewmh_obj.getClientList()
            if not windows:
                return None
            
            for window in windows:
                try:
                    # 获取窗口名称
                    window_name = self.ewmh_obj.getWmName(window)
                    if not window_name:
                        # 尝试旧的方法
                        window_name = window.get_wm_name()
                    
                    if window_name:
                        # 匹配窗口标题
                        if exact_match:
                            if window_name == title:
                                return window
                        else:
                            if title.lower() in window_name.lower():
                                return window
                except Exception:
                    continue
            
            return None
        except Exception as e:
            logger.error(f"_find_window_by_title error: {e}")
            return None
    
    def is_focus_valid(self, game_title: str = "The Bazaar") -> bool:
        """
        检查前台窗口是否为游戏或本应用
        """
        if not self.display or not self.ewmh_obj:
            return False
        
        try:
            # 获取当前活动窗口
            active_window = self.ewmh_obj.getActiveWindow()
            if not active_window:
                return False
            
            # 1. 检查窗口标题
            window_name = self.ewmh_obj.getWmName(active_window)
            if not window_name:
                window_name = active_window.get_wm_name()
            
            if window_name and game_title.lower() in window_name.lower():
                return True
            
            # 2. 检查 PID（是否为本应用）
            try:
                # 获取窗口的 PID
                wm_pid = active_window.get_full_property(
                    self.display.intern_atom('_NET_WM_PID'), X.AnyPropertyType
                )
                if wm_pid and wm_pid.value:
                    window_pid = wm_pid.value[0]
                    if window_pid == self._get_pid():
                        return True
            except Exception:
                pass
            
            return False
        except Exception as e:
            logger.error(f"is_focus_valid error: {e}")
            return False
    
    def get_window_rect(self, window_title: str, exact_match: bool = False) -> Optional[Tuple[int, int, int, int]]:
        """
        获取窗口的客户区矩形
        
        注意：返回的是窗口框架的位置，可能包含标题栏
        """
        if not self.display or not self.ewmh_obj:
            return None
        
        try:
            window = self._find_window_by_title(window_title, exact_match)
            if not window:
                return None
            
            # 获取窗口几何信息
            geometry = window.get_geometry()
            
            # 获取窗口在屏幕上的绝对位置
            # translate_coords 将窗口坐标转换为根窗口坐标
            root = self.display.screen().root
            coords = window.translate_coords(root, 0, 0)
            
            x = coords.x
            y = coords.y
            w = geometry.width
            h = geometry.height
            
            # 如果需要获取客户区（不包含边框和标题栏），可以使用 extents
            try:
                frame_extents = window.get_full_property(
                    self.display.intern_atom('_NET_FRAME_EXTENTS'), X.AnyPropertyType
                )
                if frame_extents and frame_extents.value:
                    # _NET_FRAME_EXTENTS: left, right, top, bottom
                    left, right, top, bottom = frame_extents.value[:4]
                    # 调整为客户区
                    x += left
                    y += top
                    w -= (left + right)
                    h -= (top + bottom)
            except Exception:
                pass
            
            return (x, y, w, h)
        except Exception as e:
            logger.error(f"get_window_rect error: {e}")
            return None
    
    def get_mouse_pos_relative(self, window_x: int, window_y: int) -> Tuple[int, int]:
        """
        获取相对于窗口的鼠标位置
        """
        if not self.display:
            return (0, 0)
        
        try:
            # 获取鼠标在根窗口的位置
            root = self.display.screen().root
            pointer = root.query_pointer()
            
            mouse_x = pointer.root_x
            mouse_y = pointer.root_y
            
            return (mouse_x - window_x, mouse_y - window_y)
        except Exception as e:
            logger.error(f"get_mouse_pos_relative error: {e}")
            return (0, 0)
    
    def is_window_foreground(self, window_title: str) -> bool:
        """
        检查指定窗口是否在前台
        """
        if not self.display or not self.ewmh_obj:
            return False
        
        try:
            active_window = self.ewmh_obj.getActiveWindow()
            if not active_window:
                return False
            
            window_name = self.ewmh_obj.getWmName(active_window)
            if not window_name:
                window_name = active_window.get_wm_name()
            
            return window_name and window_title.lower() in window_name.lower()
        except Exception as e:
            logger.error(f"is_window_foreground error: {e}")
            return False
    
    def get_foreground_window_title(self) -> str:
        """
        获取前台窗口标题
        """
        if not self.display or not self.ewmh_obj:
            return ""
        
        try:
            active_window = self.ewmh_obj.getActiveWindow()
            if not active_window:
                return ""
            
            window_name = self.ewmh_obj.getWmName(active_window)
            if not window_name:
                window_name = active_window.get_wm_name()
            
            return window_name or ""
        except Exception as e:
            logger.error(f"get_foreground_window_title error: {e}")
            return ""
    
    def restore_focus_to_game(self, game_title: str = "The Bazaar") -> bool:
        """
        恢复焦点到游戏窗口
        """
        if not self.display or not self.ewmh_obj:
            return False
        
        try:
            window = self._find_window_by_title(game_title)
            if not window:
                return False
            
            # 激活窗口
            self.ewmh_obj.setActiveWindow(window)
            self.display.flush()
            
            return True
        except Exception as e:
            logger.error(f"restore_focus_to_game error: {e}")
            return False
    
    def __del__(self):
        """清理资源"""
        try:
            if self.display:
                self.display.close()
        except Exception:
            pass
