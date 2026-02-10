"""
Windows 平台游戏日志路径实现
"""
import os
from pathlib import Path
from typing import Optional
from loguru import logger

from platforms.interfaces.game_log import GameLogPathProvider


class WindowsGameLogPathProvider(GameLogPathProvider):
    """
    Windows 平台日志路径提供者
    
    游戏日志位置：
    %USERPROFILE%\\AppData\\LocalLow\\Tempo Storm\\The Bazaar\\Player.log
    """
    
    def __init__(self):
        self._log_dir: Optional[Path] = None
        self._initialize()
    
    def _initialize(self):
        """初始化日志目录路径"""
        try:
            # 获取用户配置文件目录
            userprofile = os.environ.get('USERPROFILE')
            if not userprofile:
                logger.warning("Windows: 无法获取 USERPROFILE 环境变量")
                return
            
            # 构建完整路径
            self._log_dir = Path(userprofile) / "AppData" / "LocalLow" / "Tempo Storm" / "The Bazaar"
            
            if self._log_dir.exists():
                logger.info(f"Windows: 找到游戏日志目录: {self._log_dir}")
            else:
                logger.warning(f"Windows: 日志目录不存在: {self._log_dir}")
                
        except Exception as e:
            logger.error(f"Windows: 初始化日志路径失败: {e}")
            self._log_dir = None
    
    def get_log_directory(self) -> Optional[Path]:
        """获取游戏日志目录"""
        return self._log_dir
    
    def get_player_log_path(self) -> Optional[Path]:
        """获取 Player.log 路径"""
        if self._log_dir is None:
            return None
        return self._log_dir / "Player.log"
    
    def get_player_prev_log_path(self) -> Optional[Path]:
        """获取 Player-prev.log 路径"""
        if self._log_dir is None:
            return None
        return self._log_dir / "Player-prev.log"
