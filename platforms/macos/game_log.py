"""
macOS 平台游戏日志路径实现
"""
import os
from pathlib import Path
from typing import Optional
from loguru import logger

from platforms.interfaces.game_log import GameLogPathProvider


class MacOSGameLogPathProvider(GameLogPathProvider):
    """
    macOS 平台日志路径提供者
    
    游戏日志位置：
    ~/Library/Logs/Tempo Storm/The Bazaar/Player.log
    """
    
    def __init__(self):
        self._log_dir: Optional[Path] = None
        self._initialize()
    
    def _initialize(self):
        """初始化日志目录路径"""
        try:
            # 获取用户主目录
            home = os.environ.get('HOME')
            if not home:
                home = str(Path.home())
            
            if not home:
                logger.warning("macOS: 无法获取 HOME 目录")
                return
            
            # 构建完整路径
            self._log_dir = Path(home) / "Library" / "Logs" / "Tempo Storm" / "The Bazaar"
            
            if self._log_dir.exists():
                logger.info(f"macOS: 找到游戏日志目录: {self._log_dir}")
            else:
                logger.warning(f"macOS: 日志目录不存在: {self._log_dir}")
                logger.info("macOS: 如果游戏已安装，请确保至少运行过一次游戏")
                
        except Exception as e:
            logger.error(f"macOS: 初始化日志路径失败: {e}")
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
