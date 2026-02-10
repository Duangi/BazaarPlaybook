"""
游戏日志路径接口定义
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class GameLogPathProvider(ABC):
    """游戏日志路径提供者接口"""
    
    @abstractmethod
    def get_log_directory(self) -> Optional[Path]:
        """
        获取游戏日志目录
        
        Returns:
            Path: 日志目录路径，如果无法确定则返回 None
        """
        pass
    
    @abstractmethod
    def get_player_log_path(self) -> Optional[Path]:
        """
        获取 Player.log 完整路径
        
        Returns:
            Path: Player.log 文件路径，如果无法确定则返回 None
        """
        pass
    
    @abstractmethod
    def get_player_prev_log_path(self) -> Optional[Path]:
        """
        获取 Player-prev.log 完整路径
        
        Returns:
            Path: Player-prev.log 文件路径，如果无法确定则返回 None
        """
        pass
    
    def validate_log_directory(self) -> bool:
        """
        验证日志目录是否存在
        
        Returns:
            bool: 目录是否存在
        """
        log_dir = self.get_log_directory()
        return log_dir is not None and log_dir.exists()


class NullGameLogPathProvider(GameLogPathProvider):
    """空实现：当平台不支持时使用"""
    
    def get_log_directory(self) -> Optional[Path]:
        return None
    
    def get_player_log_path(self) -> Optional[Path]:
        return None
    
    def get_player_prev_log_path(self) -> Optional[Path]:
        return None
