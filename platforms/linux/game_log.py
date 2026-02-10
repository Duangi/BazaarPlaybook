"""
Linux 平台游戏日志路径实现（包括 Steam Deck）
"""
import os
from pathlib import Path
from typing import Optional
from loguru import logger

from platforms.interfaces.game_log import GameLogPathProvider


class LinuxGameLogPathProvider(GameLogPathProvider):
    """
    Linux 平台日志路径提供者（包括 Steam Deck）
    
    可能的日志位置（按优先级）：
    1. ~/.config/unity3d/Tempo Storm/The Bazaar/Player.log (Unity 标准路径)
    2. ~/.local/share/unity3d/Tempo Storm/The Bazaar/Player.log (备选路径)
    3. Steam 兼容层路径 (Proton/Wine):
       - ~/.steam/steam/steamapps/compatdata/<APPID>/pfx/drive_c/users/steamuser/AppData/LocalLow/Tempo Storm/The Bazaar/Player.log
    4. Steam Deck 特定路径：
       - /home/deck/.steam/steam/steamapps/compatdata/<APPID>/pfx/drive_c/users/steamuser/AppData/LocalLow/Tempo Storm/The Bazaar/Player.log
    
    注意：如果游戏通过 Proton/Wine 运行，日志路径会在兼容层目录中
    """
    
    # The Bazaar 的 Steam App ID（需要根据实际游戏确认）
    # 如果不确定，可以留空，让用户手动配置
    STEAM_APP_ID = None  # 例如: "123456"
    
    def __init__(self):
        self._log_dir: Optional[Path] = None
        self._initialize()
    
    def _initialize(self):
        """初始化日志目录路径，尝试多个可能的位置"""
        try:
            home = os.environ.get('HOME')
            if not home:
                home = str(Path.home())
            
            if not home:
                logger.warning("Linux: 无法获取 HOME 目录")
                return
            
            home_path = Path(home)
            
            # 可能的日志路径列表（按优先级）
            possible_paths = []
            
            # 1. Unity 标准配置路径
            possible_paths.append(
                home_path / ".config" / "unity3d" / "Tempo Storm" / "The Bazaar"
            )
            
            # 2. Unity 备选数据路径
            possible_paths.append(
                home_path / ".local" / "share" / "unity3d" / "Tempo Storm" / "The Bazaar"
            )
            
            # 3. Steam Proton 兼容层路径（如果知道 App ID）
            if self.STEAM_APP_ID:
                steam_compat_path = (
                    home_path / ".steam" / "steam" / "steamapps" / "compatdata" / 
                    self.STEAM_APP_ID / "pfx" / "drive_c" / "users" / "steamuser" / 
                    "AppData" / "LocalLow" / "Tempo Storm" / "The Bazaar"
                )
                possible_paths.append(steam_compat_path)
            
            # 4. 尝试自动查找 Steam 兼容层目录（遍历所有 compatdata）
            steam_compatdata = home_path / ".steam" / "steam" / "steamapps" / "compatdata"
            if steam_compatdata.exists():
                for app_dir in steam_compatdata.iterdir():
                    if app_dir.is_dir():
                        proton_log_path = (
                            app_dir / "pfx" / "drive_c" / "users" / "steamuser" / 
                            "AppData" / "LocalLow" / "Tempo Storm" / "The Bazaar"
                        )
                        if proton_log_path.exists():
                            possible_paths.insert(0, proton_log_path)  # 优先使用找到的路径
            
            # 5. Steam Deck 特定路径（deck 用户）
            if home == "/home/deck":
                deck_path = (
                    Path("/home/deck") / ".steam" / "steam" / "steamapps" / "compatdata"
                )
                if deck_path.exists():
                    logger.info("Linux: 检测到 Steam Deck 环境")
                    # deck 环境已经在步骤 4 中处理
            
            # 6. Flatpak Steam 路径
            flatpak_steam = home_path / ".var" / "app" / "com.valvesoftware.Steam" / ".steam" / "steam" / "steamapps" / "compatdata"
            if flatpak_steam.exists():
                for app_dir in flatpak_steam.iterdir():
                    if app_dir.is_dir():
                        flatpak_log_path = (
                            app_dir / "pfx" / "drive_c" / "users" / "steamuser" / 
                            "AppData" / "LocalLow" / "Tempo Storm" / "The Bazaar"
                        )
                        if flatpak_log_path.exists():
                            possible_paths.insert(0, flatpak_log_path)
            
            # 遍历所有可能的路径，找到第一个存在的
            for path in possible_paths:
                if path.exists():
                    self._log_dir = path
                    logger.info(f"Linux: 找到游戏日志目录: {self._log_dir}")
                    return
            
            # 如果都不存在，使用默认的 Unity 标准路径（即使不存在）
            self._log_dir = possible_paths[0] if possible_paths else None
            if self._log_dir:
                logger.warning(f"Linux: 日志目录不存在，使用默认路径: {self._log_dir}")
                logger.info("Linux: 可能的原因：")
                logger.info("  1. 游戏尚未运行过")
                logger.info("  2. 游戏通过 Proton/Wine 运行（需要找到对应的 compatdata 目录）")
                logger.info("  3. 使用了自定义的 Steam 库路径")
                logger.info(f"Linux: 已检查的路径: {[str(p) for p in possible_paths[:3]]}")
            else:
                logger.error("Linux: 无法确定日志路径")
                
        except Exception as e:
            logger.error(f"Linux: 初始化日志路径失败: {e}")
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
    
    def set_steam_app_id(self, app_id: str):
        """
        设置 Steam App ID 以便定位 Proton 兼容层路径
        
        Args:
            app_id: Steam App ID（例如 "123456"）
        """
        self.STEAM_APP_ID = app_id
        self._initialize()  # 重新初始化路径
