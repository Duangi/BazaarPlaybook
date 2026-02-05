"""
野怪数据加载器 (Monster Data Loader)
从 monsters_db.json 加载野怪数据
"""
import json
import os
from typing import List, Dict, Any, Optional


class Monster:
    """野怪数据类"""
    
    def __init__(self, data: Dict[str, Any], name_key: str):
        self.name_key = name_key  # 中文名作为 key
        self.name_zh = data.get("name_zh", name_key)
        self.name_en = data.get("name", "")
        self.available = data.get("available", "Day 1")  # Day 1, Day 2, etc.
        self.health = data.get("health", 100)
        self.tags = data.get("tags", [])
        self.level = data.get("level", 1)
        self.combat = data.get("combat", {})
        self.skills = data.get("skills", [])
        self.items = data.get("items", [])
        
        # 提取 day 数字
        self.day = self._extract_day_number(self.available)
    
    def _extract_day_number(self, available: str) -> int:
        """从 'Day 1', 'Day 10+' 提取数字"""
        if not available:
            return 1
        try:
            # 提取数字部分
            day_str = available.replace("Day", "").replace("+", "").strip()
            return int(day_str) if day_str.isdigit() else 1
        except:
            return 1
    
    def get_gold_reward(self) -> str:
        """获取金币奖励"""
        return self.combat.get("gold", "0 Gold")
    
    def get_exp_reward(self) -> str:
        """获取经验奖励"""
        return self.combat.get("exp", "0 XP")
    
    def get_image_path(self) -> str:
        """获取怪物图片路径"""
        # 图片存储在 assets/images/monster_char/ 目录
        # 文件名格式通常是怪物的英文名或ID
        base_path = "assets/images/monster_char"
        
        # 尝试多种命名方式
        possible_names = [
            self.name_en.lower().replace(" ", "_"),
            self.name_zh,
            f"monster_{self.level}"
        ]
        
        for name in possible_names:
            for ext in [".webp", ".png", ".jpg"]:
                path = os.path.join(base_path, name + ext)
                if os.path.exists(path):
                    return path
        
        # 如果没找到，返回默认图片
        return "assets/images/monster_char/default.webp"


class MonsterDatabase:
    """野怪数据库"""
    
    def __init__(self, json_path: str = "assets/json/monsters_db.json"):
        self.json_path = json_path
        self.monsters: List[Monster] = []
        self.monsters_by_day: Dict[int, List[Monster]] = {}
        self._load_data()
    
    def _load_data(self):
        """加载 JSON 数据"""
        if not os.path.exists(self.json_path):
            print(f"[MonsterDB] Warning: {self.json_path} not found")
            return
        
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 解析每个怪物
            for name_key, monster_data in data.items():
                monster = Monster(monster_data, name_key)
                self.monsters.append(monster)
                
                # 按天分组
                day = monster.day
                if day not in self.monsters_by_day:
                    self.monsters_by_day[day] = []
                self.monsters_by_day[day].append(monster)
            
            print(f"[MonsterDB] Loaded {len(self.monsters)} monsters")
            print(f"[MonsterDB] Days: {sorted(self.monsters_by_day.keys())}")
        
        except Exception as e:
            print(f"[MonsterDB] Error loading data: {e}")
    
    def get_monsters_by_day(self, day: int) -> List[Monster]:
        """获取指定天数的怪物列表"""
        return self.monsters_by_day.get(day, [])
    
    def get_all_days(self) -> List[int]:
        """获取所有天数（排序）"""
        return sorted(self.monsters_by_day.keys())
    
    def get_monster_by_name(self, name: str) -> Optional[Monster]:
        """根据名字查找怪物"""
        for monster in self.monsters:
            if monster.name_zh == name or monster.name_en == name:
                return monster
        return None


# 全局单例
_monster_db = None

def get_monster_db() -> MonsterDatabase:
    """获取全局怪物数据库实例"""
    global _monster_db
    if _monster_db is None:
        _monster_db = MonsterDatabase()
    return _monster_db
