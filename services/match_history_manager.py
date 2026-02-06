"""
战绩管理器
用于保存和读取游戏战绩数据
"""
import json
import uuid
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class MatchHistoryManager:
    """战绩历史管理器"""
    
    def __init__(self, data_dir: str = None):
        """
        初始化战绩管理器
        
        Args:
            data_dir: 数据目录，默认为user_data
        """
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "user_data"
        else:
            data_dir = Path(data_dir)
        
        self.data_dir = data_dir
        self.history_file = self.data_dir / "match_history.json"
        self.screenshot_dir = self.data_dir / "match_screenshots"
        
        # 确保目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        # 确保历史文件存在
        if not self.history_file.exists():
            self._save_history({"matches": []})
    
    def _load_history(self) -> Dict:
        """加载历史数据"""
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading match history: {e}")
            return {"matches": []}
    
    def _save_history(self, data: Dict):
        """保存历史数据"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving match history: {e}")
    
    def add_match(self, session_data: Dict, hero: str = "Unknown") -> str:
        """
        添加一场对局记录
        
        Args:
            session_data: 从LogAnalyzer获取的session数据
            hero: 使用的英雄名称
            
        Returns:
            match_id: 对局唯一ID
        """
        history = self._load_history()
        
        # 生成唯一ID
        match_id = str(uuid.uuid4())
        
        # 构建对局数据
        match_record = {
            "match_id": match_id,
            "hero": hero,
            "start_time": session_data.get("start_time", ""),
            "end_time": session_data.get("end_time", ""),
            "days": session_data.get("days", 0),
            "victory": session_data.get("victory", False),
            "is_finished": session_data.get("is_finished", False),
            "created_at": datetime.now().isoformat(),
            "pvp_battles": []
        }
        
        # 添加PVP战斗记录
        for pvp in session_data.get("pvp_battles", []):
            battle_record = {
                "day": pvp.get("day", 0),
                "start_time": pvp.get("start_time", ""),
                "victory": False,  # 暂时无法判断单场PVP胜负，需要后续补充
                "player_items": pvp.get("player_items", []),
                "opponent_items": pvp.get("opponent_items", []),
                "screenshot": None  # 截图路径，初始为None
            }
            match_record["pvp_battles"].append(battle_record)
        
        # 添加到历史记录
        history["matches"].insert(0, match_record)  # 新记录插入到最前面
        
        # 保存
        self._save_history(history)
        
        return match_id
    
    def get_all_matches(self) -> List[Dict]:
        """获取所有对局记录"""
        history = self._load_history()
        return history.get("matches", [])
    
    def get_match(self, match_id: str) -> Optional[Dict]:
        """获取指定对局记录"""
        matches = self.get_all_matches()
        for match in matches:
            if match.get("match_id") == match_id:
                return match
        return None
    
    def update_match(self, match_id: str, updates: Dict):
        """更新对局记录"""
        history = self._load_history()
        matches = history.get("matches", [])
        
        for i, match in enumerate(matches):
            if match.get("match_id") == match_id:
                matches[i].update(updates)
                self._save_history(history)
                return True
        
        return False
    
    def update_battle_screenshot(self, match_id: str, day: int, screenshot_path: str):
        """更新某一天的截图路径"""
        history = self._load_history()
        matches = history.get("matches", [])
        
        for match in matches:
            if match.get("match_id") == match_id:
                for battle in match.get("pvp_battles", []):
                    if battle.get("day") == day:
                        battle["screenshot"] = screenshot_path
                        self._save_history(history)
                        return True
        
        return False
    
    def delete_match(self, match_id: str) -> bool:
        """删除对局记录"""
        history = self._load_history()
        matches = history.get("matches", [])
        
        # 查找并删除
        new_matches = [m for m in matches if m.get("match_id") != match_id]
        
        if len(new_matches) < len(matches):
            history["matches"] = new_matches
            self._save_history(history)
            return True
        
        return False
    
    def get_screenshot_path(self, match_id: str, day: int) -> Path:
        """获取截图保存路径"""
        return self.screenshot_dir / f"{match_id}_day{day}.png"
