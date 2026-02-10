from abc import ABC, abstractmethod
from typing import Optional, Tuple

class WindowManager(ABC):
    """
    窗口管理器接口：跨平台窗口操作抽象
    """
    
    @abstractmethod
    def is_focus_valid(self, game_title: str = "The Bazaar") -> bool:
        """
        检查焦点窗口是否有效（游戏窗口或应用自身）
        
        Args:
            game_title: 游戏窗口标题
            
        Returns:
            bool: 焦点是否有效
        """
        pass
    
    @abstractmethod
    def get_window_rect(self, window_title: str, exact_match: bool = False) -> Optional[Tuple[int, int, int, int]]:
        """
        获取窗口的客户区矩形
        
        Args:
            window_title: 窗口标题
            exact_match: 是否精确匹配标题
            
        Returns:
            Optional[Tuple[int, int, int, int]]: (x, y, width, height) 或 None
        """
        pass
    
    @abstractmethod
    def get_mouse_pos_relative(self, window_x: int, window_y: int) -> Tuple[int, int]:
        """
        获取相对于窗口的鼠标位置
        
        Args:
            window_x: 窗口 X 坐标
            window_y: 窗口 Y 坐标
            
        Returns:
            Tuple[int, int]: 相对坐标 (x, y)
        """
        pass
    
    @abstractmethod
    def is_window_foreground(self, window_title: str) -> bool:
        """
        检查指定标题的窗口是否在前台
        
        Args:
            window_title: 窗口标题
            
        Returns:
            bool: 是否在前台
        """
        pass
    
    @abstractmethod
    def get_foreground_window_title(self) -> str:
        """
        获取前台窗口标题
        
        Returns:
            str: 窗口标题
        """
        pass
    
    @abstractmethod
    def restore_focus_to_game(self, game_title: str = "The Bazaar") -> bool:
        """
        恢复焦点到游戏窗口
        
        Args:
            game_title: 游戏窗口标题
            
        Returns:
            bool: 是否成功
        """
        pass


class NullWindowManager(WindowManager):
    """空实现：防止系统崩溃"""
    
    def is_focus_valid(self, game_title: str = "The Bazaar") -> bool:
        return False
    
    def get_window_rect(self, window_title: str, exact_match: bool = False) -> Optional[Tuple[int, int, int, int]]:
        return None
    
    def get_mouse_pos_relative(self, window_x: int, window_y: int) -> Tuple[int, int]:
        return (0, 0)
    
    def is_window_foreground(self, window_title: str) -> bool:
        return False
    
    def get_foreground_window_title(self) -> str:
        return ""
    
    def restore_focus_to_game(self, game_title: str = "The Bazaar") -> bool:
        return False
