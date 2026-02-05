# gui/data/data_loader.py
"""数据加载器 - 从JSON文件加载物品、技能、怪物数据"""
import json
import os
from pathlib import Path
from typing import Dict, List, Any

class DataLoader:
    """数据加载器单例"""
    
    _instance = None
    _items_db: List[Dict] = []
    _skills_db: List[Dict] = []
    _monsters_db: Dict[str, Dict] = {}
    _loaded = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._loaded:
            self.load_all()
    
    def load_all(self):
        """加载所有数据"""
        base_path = Path(__file__).parent.parent.parent / "assets" / "json"
        
        # 加载物品数据库
        items_path = base_path / "items_db.json"
        if items_path.exists():
            with open(items_path, 'r', encoding='utf-8') as f:
                self._items_db = json.load(f)
                print(f"[DataLoader] Loaded {len(self._items_db)} items")
        
        # 加载技能数据库
        skills_path = base_path / "skills_db.json"
        if skills_path.exists():
            with open(skills_path, 'r', encoding='utf-8') as f:
                self._skills_db = json.load(f)
                print(f"[DataLoader] Loaded {len(self._skills_db)} skills")
        
        # 加载怪物数据库
        monsters_path = base_path / "monsters_db.json"
        if monsters_path.exists():
            with open(monsters_path, 'r', encoding='utf-8') as f:
                self._monsters_db = json.load(f)
                print(f"[DataLoader] Loaded {len(self._monsters_db)} monsters")
        
        self._loaded = True
    
    def get_monsters_by_day(self, day: int) -> List[Dict]:
        """获取指定天数的怪物列表"""
        result = []
        
        for name_zh, data in self._monsters_db.items():
            available = data.get('available', '')
            
            # 解析可用天数
            if 'Day' in available:
                day_str = available.replace('Day', '').strip()
                
                if '-' in day_str:
                    # 范围格式: "Day 1-5"
                    start, end = day_str.split('-')
                    if day >= int(start) and day <= int(end):
                        result.append(self._parse_monster(name_zh, data))
                elif '+' in day_str:
                    # 开放格式: "Day 10+"
                    min_day = int(day_str.replace('+', '').strip())
                    if day >= min_day:
                        result.append(self._parse_monster(name_zh, data))
                else:
                    # 单个天数: "Day 3"
                    if day == int(day_str):
                        result.append(self._parse_monster(name_zh, data))
        
        return result
    
    def _parse_monster(self, name_zh: str, data: Dict) -> Dict:
        """解析怪物数据为标准格式"""
        # 解析可用天数为列表
        available_list = self._parse_available_days(data.get('available', ''))
        
        return {
            'id': name_zh,  # 使用中文名作为ID
            'name_zh': name_zh,
            'name_en': data.get('name', ''),
            'hp': data.get('health', 0),
            'max_hp': data.get('health', 0),
            'available': available_list,
            'level': data.get('level', 1),
            'gold': data.get('combat', {}).get('gold', '0 Gold'),
            'exp': data.get('combat', {}).get('exp', '0 XP'),
            'bg_path': self._get_monster_bg_path(name_zh),
            'char_path': self._get_monster_char_path(name_zh),
            'skills': self._parse_monster_skills(data.get('skills', [])),
            'items': self._parse_monster_items(data.get('items', []))
        }
    
    def _parse_available_days(self, available: str) -> List[int]:
        """解析可用天数字符串为天数列表"""
        if not available or 'Day' not in available:
            return []
        
        day_str = available.replace('Day', '').strip()
        
        if '-' in day_str:
            # 范围格式: "1-5"
            start, end = day_str.split('-')
            return list(range(int(start), int(end) + 1))
        elif '+' in day_str:
            # 开放格式: "10+"
            min_day = int(day_str.replace('+', '').strip())
            return list(range(min_day, 21))  # 假设最大20天
        else:
            # 单个天数
            return [int(day_str)]
    
    def _get_monster_bg_path(self, name_zh: str) -> str:
        """获取怪物背景图路径"""
        # 这里需要根据实际文件映射
        # 暂时返回空，后续需要建立名称到文件的映射
        base_path = Path(__file__).parent.parent.parent / "assets" / "images" / "monster_bg"
        # TODO: 建立怪物名称到背景图的映射
        return ""
    
    def _get_monster_char_path(self, name_zh: str) -> str:
        """获取怪物角色图路径"""
        base_path = Path(__file__).parent.parent.parent / "assets" / "images" / "monster_char"
        # TODO: 建立怪物名称到角色图的映射
        return ""
    
    def _parse_monster_skills(self, skills: List[Dict]) -> List[Dict]:
        """解析怪物技能列表"""
        result = []
        
        for skill in skills:
            tier = skill.get('current_tier', 'bronze').lower()
            tier_data = skill.get('tiers', {}).get(tier, {})
            
            # 获取描述
            descriptions = tier_data.get('description', [])
            desc_text = '\n'.join(descriptions) if descriptions else ''
            
            # 获取额外描述
            extra = tier_data.get('extra_description', [])
            if extra:
                desc_text += '\n' + '\n'.join(extra)
            
            # 获取图片路径
            image_path = skill.get('image', '')
            if image_path:
                full_path = Path(__file__).parent.parent.parent / "assets" / image_path
                image_path = str(full_path) if full_path.exists() else None
            
            result.append({
                'id': skill.get('id', ''),
                'name_zh': skill.get('name', ''),
                'name_en': skill.get('name_en', ''),
                'tier': skill.get('tier', 'Bronze+'),
                'current_tier': tier,
                'size': 'medium',  # 技能默认中型
                'cooldown': tier_data.get('cd', 0) or 0,
                'description': desc_text,
                'image_path': image_path,
                'tags': skill.get('tags', [])
            })
        
        return result
    
    def _parse_monster_items(self, items: List[Dict]) -> List[Dict]:
        """解析怪物物品列表"""
        result = []
        
        for item in items:
            tier = item.get('current_tier', 'bronze').lower()
            tier_data = item.get('tiers', {}).get(tier, {})
            
            if tier_data is None:
                continue
            
            # 获取描述
            descriptions = tier_data.get('description', [])
            desc_text = '\n'.join(descriptions) if descriptions else ''
            
            # 获取额外描述
            extra = tier_data.get('extra_description', [])
            if extra:
                desc_text += '\n' + '\n'.join(extra)
            
            result.append({
                'id': item.get('id', ''),
                'name_zh': item.get('name', ''),
                'tier': item.get('tier', 'Bronze+'),
                'current_tier': tier,
                'size': 'small',  # 怪物掉落默认小型
                'cooldown': tier_data.get('cd', 0) or 0,
                'description': desc_text,
                'image_path': None,  # 物品图片需要从items_db匹配
                'tags': item.get('tags', [])
            })
        
        return result
    
    def search_items(self, keyword: str = '', tier: str = '', hero: str = '', 
                    item_type: str = 'all', size: str = '', tags: List[str] = None) -> List[Dict]:
        """搜索物品"""
        results = []
        
        # 搜索物品数据库
        if item_type in ['all', 'item']:
            for item in self._items_db:
                if not self._match_item(item, keyword, tier, hero, size, tags):
                    continue
                    
                results.append(self._format_item(item))
        
        # 搜索技能数据库
        if item_type in ['all', 'skill']:
            for skill in self._skills_db:
                if not self._match_skill(skill, keyword, tier, hero, tags):
                    continue
                    
                results.append(self._format_skill(skill))
        
        return results
    
    def _match_item(self, item: Dict, keyword: str, tier: str, hero: str, 
                   size: str, tags: List[str]) -> bool:
        """判断物品是否匹配搜索条件"""
        # 关键词匹配
        if keyword:
            keyword_lower = keyword.lower()
            if (keyword_lower not in item.get('name_cn', '').lower() and
                keyword_lower not in item.get('name_en', '').lower()):
                return False
        
        # 阶级匹配
        if tier:
            item_tier = item.get('starting_tier', '').split('/')[0].strip().lower()
            if tier.lower() not in item_tier:
                return False
        
        # 英雄匹配
        if hero:
            item_heroes = item.get('heroes', '')
            if hero not in item_heroes:
                return False
        
        # 尺寸匹配
        if size:
            item_size = item.get('size', '').split('/')[0].strip().lower()
            if size.lower() not in item_size:
                return False
        
        # 标签匹配
        if tags:
            item_tags = item.get('tags', '').lower()
            for tag in tags:
                if tag.lower() not in item_tags:
                    return False
        
        return True
    
    def _match_skill(self, skill: Dict, keyword: str, tier: str, 
                    hero: str, tags: List[str]) -> bool:
        """判断技能是否匹配搜索条件"""
        # 关键词匹配
        if keyword:
            keyword_lower = keyword.lower()
            if (keyword_lower not in skill.get('name_cn', '').lower() and
                keyword_lower not in skill.get('name_en', '').lower()):
                return False
        
        # 阶级匹配
        if tier:
            skill_tier = skill.get('starting_tier', '').split('/')[0].strip().lower()
            if tier.lower() not in skill_tier:
                return False
        
        # 英雄匹配
        if hero:
            skill_heroes = skill.get('heroes', '')
            if hero not in skill_heroes:
                return False
        
        return True
    
    def _format_item(self, item: Dict) -> Dict:
        """格式化物品数据"""
        # 获取图片路径
        image_path = self._get_item_image_path(item.get('id', ''))
        
        # 解析技能描述
        skills = item.get('skills', [])
        description = '\n'.join([s.get('cn', '') for s in skills])
        
        # 解析附魔
        enchantments = []
        enchant_data = item.get('enchantments', {})
        for enchant_type, enchant_info in enchant_data.items():
            if isinstance(enchant_info, dict):
                enchantments.append({
                    'type': enchant_type,
                    'effect': enchant_info.get('effect_cn', '')
                })
        
        return {
            'id': item.get('id', ''),
            'name_zh': item.get('name_cn', ''),
            'name_en': item.get('name_en', ''),
            'tier': item.get('starting_tier', 'Bronze / 青铜'),
            'size': item.get('size', 'Medium / 中型'),
            'hero': item.get('heroes', 'Common / 通用'),
            'tags': item.get('tags', '').split(' | ') if item.get('tags') else [],
            'cooldown': item.get('cooldown', 0) / 1000,  # 转换为秒
            'description': description,
            'image_path': image_path,
            'enchantments': enchantments
        }
    
    def _format_skill(self, skill: Dict) -> Dict:
        """格式化技能数据"""
        # 获取图片路径
        art_key = skill.get('art_key', '')
        image_path = self._get_skill_image_path(art_key)
        
        # 解析描述
        descriptions = skill.get('descriptions', [])
        description = '\n'.join([d.get('cn', '') for d in descriptions])
        
        return {
            'id': skill.get('id', ''),
            'name_zh': skill.get('name_cn', ''),
            'name_en': skill.get('name_en', ''),
            'tier': skill.get('starting_tier', 'Bronze / 青铜'),
            'size': skill.get('size', 'Medium / 中型'),
            'hero': skill.get('heroes', 'Common / 通用'),
            'tags': [],
            'cooldown': 0,
            'description': description,
            'image_path': image_path,
            'enchantments': []
        }
    
    def _get_item_image_path(self, item_id: str) -> str:
        """获取物品图片路径"""
        if not item_id:
            return None
            
        base_path = Path(__file__).parent.parent.parent / "assets" / "images" / "card"
        image_file = base_path / f"{item_id}.webp"
        
        if image_file.exists():
            return str(image_file)
        return None
    
    def _get_skill_image_path(self, art_key: str) -> str:
        """获取技能图片路径"""
        if not art_key:
            return None
            
        base_path = Path(__file__).parent.parent.parent / "assets" / "images" / "skill"
        image_file = base_path / art_key
        
        if image_file.exists():
            return str(image_file)
        return None


# 全局单例
data_loader = DataLoader()
