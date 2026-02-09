"""
物品详情卡片组件 (Item Detail Card) - 最终版
功能：展示物品/技能的详细信息，支持展开/折叠，完美复刻React版样式
"""
from typing import Dict, List, Union
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QPushButton, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QColor
from pathlib import Path
import json
import re


class ItemDetailCard(QFrame):
    """
    物品详情卡片组件 - 1:1 复刻设计
    """
    
    def __init__(self, item_id: str = None, item_type: str = "skill", 
                 current_tier: str = "bronze", parent=None, default_expanded: bool = False,
                 enable_tier_click: bool = False, content_scale: float = 1.0, item_data: Dict = None):
        super().__init__(parent)
        # 兼容旧接口
        if item_data is None and item_id:
             # 如果只传了ID没传data (理论上现在都传data了)，留个空fallback
             pass
             
        self.item_data = item_data or {}
        self.content_scale = content_scale
        self.is_expanded = default_expanded
        
        self.setObjectName("ItemDetailCard")
        # 基础样式：深色背景，微弱边框
        self.setStyleSheet(f"""
            #ItemDetailCard {{
                background: #2B2621;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-left: 0px solid transparent;
                border-radius: 6px;
            }}
            #ItemDetailCard:hover {{
                background: #322C28;
                border-left: 3px solid #ffcc00;
            }}
        """)
        
        # 始终应用 hover 效果如果已经展开 (视觉反馈)
        if self.is_expanded:
            self.setStyleSheet(f"""
                #ItemDetailCard {{
                    background: #322C28;
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    border-left: 3px solid #ffcc00;
                    border-radius: 6px;
                }}
            """)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 1. 头部区域
        self.header = self._create_header()
        layout.addWidget(self.header)
        
        # 2. 详情区域 (仅在展开时显示)
        self.details = self._create_details()
        self.details.setVisible(self.is_expanded)
        layout.addWidget(self.details)
    
    def _create_header(self) -> QWidget:
        """创建卡片头部"""
        header = QFrame()
        header.setCursor(Qt.CursorShape.PointingHandCursor)
        header.mousePressEvent = lambda e: self.toggle_expand()
        
        scale = self.content_scale
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(12, 8, 12, 8)
        h_layout.setSpacing(12)
        
        # 左侧图标
        icon_size = 64
        icon_label = QLabel()
        icon_label.setFixedSize(icon_size, icon_size)
        self._load_image(icon_label, self.item_data.get("id"), icon_size)
        h_layout.addWidget(icon_label)
        
        # 中间信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # 第一行：名称 + 品级
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        
        name = self.item_data.get("name_cn") or self.item_data.get("name", "Unknown")
        name_label = QLabel(name)
        name_label.setStyleSheet(f"color: white; font-weight: bold; font-family: 'Microsoft YaHei UI'; font-size: 16px;")
        top_row.addWidget(name_label)
        
        tier_label = self._create_tier_label()
        if tier_label:
            top_row.addWidget(tier_label)
        
        top_row.addStretch()
        info_layout.addLayout(top_row)
        
        # 第二行：属性标签
        tags_row = self._create_tags_row()
        info_layout.addLayout(tags_row)
        
        info_layout.addStretch()
        h_layout.addLayout(info_layout, 1)
        
        # 右侧：英雄头像 + 箭头
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        
        hero_row = QHBoxLayout()
        hero_row.setAlignment(Qt.AlignmentFlag.AlignRight)
        hero_avatar = self._create_hero_avatar()
        if hero_avatar:
            hero_row.addWidget(hero_avatar)
        right_layout.addLayout(hero_row)
        
        # 箭头放到底部或中间
        right_layout.addStretch()
        arrow_label = QLabel("▴" if self.is_expanded else "▾")
        arrow_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        arrow_label.setStyleSheet("color: #666; font-size: 12px;")
        right_layout.addWidget(arrow_label)
        
        h_layout.addLayout(right_layout)
        
        return header

    def _create_details(self) -> QWidget:
        """创建详情区域"""
        details = QFrame()
        details.setStyleSheet("background: transparent; border-top: 1px solid rgba(255, 255, 255, 0.05);")
        
        layout = QVBoxLayout(details)
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(12)
        
        # 1. 冷却 / 统计数据
        cooldown = self.item_data.get("cooldown")
        if cooldown:
            cd_layout = QHBoxLayout()
            cd_layout.setSpacing(2)
            # 大号蓝色文本
            cd_val = QLabel(str(cooldown))
            cd_val.setStyleSheet("color: #33CCFF; font-size: 24px; font-weight: bold; font-family: 'Microsoft YaHei UI';")
            # 同样字体和颜色的单位，或者小一点
            cd_unit = QLabel("秒")
            cd_unit.setStyleSheet("color: #33CCFF; font-size: 14px; padding-top: 8px; font-family: 'Microsoft YaHei UI';")
            
            cd_layout.addWidget(cd_val)
            cd_layout.addWidget(cd_unit)
            
            # 主动技能描述跟在冷却后面
            skills = self.item_data.get("skills", [])
            if skills:
                skill_text = self._extract_text(skills[0])
                if skill_text:
                    # 移除前面的数字 (例如 "10s") 如果有的话
                    # skill_text = re.sub(r'^\d+(\.\d+)?[s秒]\s*', '', skill_text)
                    
                    skill_lbl = QLabel(self._format_text(skill_text))
                    skill_lbl.setWordWrap(True)
                    skill_lbl.setStyleSheet("color: #ddd; font-size: 14px; margin-left: 10px; font-family: 'Microsoft YaHei UI'; line-height: 1.4;")
                    cd_layout.addWidget(skill_lbl, 1) # Stretch to fill
            
            cd_layout.addStretch()
            layout.addLayout(cd_layout)
        
        # 2. 附魔效果列表
        effects = self._get_effects_list()
        for name, desc, color in effects:
            row = self._create_effect_row(name, desc, color)
            layout.addWidget(row)
            
        return details

    def _create_effect_row(self, name: str, desc: str, color: str) -> QWidget:
        """创建单行效果: [Badge]Description"""
        row = QWidget()
        l = QHBoxLayout(row)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(10)
        
        # Badge
        badge = QLabel(name)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedSize(60, 24)
        
        # 解析颜色用于半透明背景
        c = QColor(color)
        bg_color = f"rgba({c.red()}, {c.green()}, {c.blue()}, 0.2)"
        
        badge.setStyleSheet(f"""
            background: {bg_color};
            color: {color};
            border: 1px solid {color};
            border-radius: 4px;
            font-weight: bold;
            font-size: 12px;
            font-family: 'Microsoft YaHei UI';
        """)
        l.addWidget(badge)
        
        # Desc
        desc_lbl = QLabel(self._format_text(desc))
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #ccc; font-size: 13px; font-family: 'Microsoft YaHei UI'; line-height: 1.4;")
        l.addWidget(desc_lbl, 1)
        
        return row

    def _format_text(self, text: str) -> str:
        """关键词高亮"""
        if not isinstance(text, str): return str(text)
        
        # 关键词映射 (可扩展)
        keywords = {
            "加速": "#00ecc3",
            "减速": "#5c7cfa",
            "冻结": "#22b8cf",
            "治疗": "#8eea31",
            "回复": "#8eea31", # Regen
            "生命值": "#8eea31",
            "剧毒": "#0ebe4f",
            "毒素": "#0ebe4f",
            "灼烧": "#ff9f45",
            "炽焰": "#ff9f45",
            "护盾": "#f4cf20",
            "价值": "#ffd700",
            "金币": "#ffd700",
            "伤害": "#f5503d",
            "暴击": "#f5503d",
            "致命": "#f5503d",
            "摧毁": "#f5503d",
            "多重触发": "#98a8fe",
            "免疫": "#ffffff"
        }
        
        # 1. 高亮数字 (黄色) - 排除 span 标签内的数字
        # 简单处理：先替换数字，再替换关键词，这样关键词可能会覆盖数字（通常是期望的），但数字颜色优先
        # 更好的策略：先处理关键词，最后处理独立的数字。
        # 这里使用简单策略：
        
        # 处理特殊的 "x 秒" 为蓝色
        # text = re.sub(r'(\d+(\.\d+)?)秒', r'<span style="color: #33CCFF; font-weight: bold;">\1秒</span>', text)

        # 高亮普通数字 (黄色)
        def replace_num(match):
            return f'<span style="color: #f59e0b; font-weight: bold;">{match.group(1)}</span>'
        text = re.sub(r'(?<!color: #)(\d+(\.\d+)?)', replace_num, text)

        
        # 2. 高亮关键词
        for kw, color in keywords.items():
            text = text.replace(kw, f'<span style="color: {color}; font-weight: bold;">{kw}</span>')
            
        return text

    def _get_effects_list(self) -> List[tuple]:
        """获取所有效果列表 [(Name, Desc, Color)]"""
        res = []
        
        # 1. Enchantments (附魔)
        enchant_map = {
            "Gold": ("黄金", "#f59e0b"),
            "Heavy": ("沉重", "#5c7cfa"), "Slow": ("沉重", "#5c7cfa"),
            "Icy": ("寒冰", "#22b8cf"), "Freeze": ("寒冰", "#22b8cf"),
            "Turbo": ("疾速", "#00ecc3"), "Haste": ("疾速", "#00ecc3"),
            "Shield": ("护盾", "#f4cf20"),
            "Restorative": ("回复", "#8eea31"), "Heal": ("回复", "#8eea31"),
            "Toxic": ("毒素", "#0ebe4f"), "Poison": ("毒素", "#0ebe4f"),
            "Fiery": ("炽焰", "#ff9f45"), "Burn": ("炽焰", "#ff9f45"),
            "Shiny": ("闪亮", "#98a8fe"), "Multicast": ("闪亮", "#98a8fe"),
            "Deadly": ("致命", "#f5503d"), "Crit": ("致命", "#f5503d"),
            "Radiant": ("辉耀", "#98a8fe"),
            "Obsidian": ("黑曜石", "#9d4a6f"), "Damage": ("黑曜石", "#9d4a6f")
        }
        
        # 尝试从 hidden_tags 或 tags 提取附魔效果
        tags = self.item_data.get("hidden_tags", []) + self.item_data.get("tags", [])
        if isinstance(tags, str): tags = [tags]
        
        processed = set()
        
        # 预定义的效果描述库 (简单模拟)
        effect_desc_db = {
            "黄金": "此物品的价值翻倍，并在战斗结束时将其25%的价值转化为金币。",
            "沉重": "每3秒，下一次攻击造成200%伤害并减速一件物品2秒。",
            "寒冰": "每3秒，下一次攻击造成200%伤害并冻结一件物品0.5秒。",
            "疾速": "此物品的冷却时间减少20%。",
            "护盾": "战斗开始时，获得40护盾。",
            "回复": "战斗开始时，治疗20生命值。",
            "毒素": "战斗开始时，施加3层剧毒。",
            "炽焰": "战斗开始时，施加3层灼烧。",
            "闪亮": "此物品的触发几率翻倍。",
            "致命": "此物品获得20%暴击率。",
            "辉耀": "此物品免疫冻结、减速和摧毁。",
            "黑曜石": "战斗开始时，造成40伤害。"
        }
        
        for tag in tags:
            for key, (name, color) in enchant_map.items():
                if key in tag and name not in processed:
                    desc = effect_desc_db.get(name, f"与{name}相关的效果")
                    res.append((name, desc, color))
                    processed.add(name)
        
        return res

    def _extract_text(self, obj) -> str:
        """从可能是dict/str的对象提取中文文本"""
        if isinstance(obj, dict):
            return obj.get("cn", obj.get("en", ""))
        return str(obj) if obj else ""

    def _create_tier_label(self) -> QLabel:
        tier_raw = self.item_data.get("tier", "Common")
        if not tier_raw: tier_raw = "Common"
        
        tier_key = tier_raw.split(" / ")[0].lower()
        
        tier_colors = {
            "bronze": ("青铜", "#cd7f32"), "common": ("青铜", "#cd7f32"),
            "silver": ("白银", "#c0c0c0"),
            "gold": ("黄金", "#ffd700"), 
            "diamond": ("钻石", "#b9f2ff"),
            "legendary": ("传说", "#ff4500"), "godly": ("神级", "#ff4500")
        }
        
        # Default to common/bronze if not found
        txt, color = tier_colors.get(tier_key, ("未知", "#888888"))
        
        if "+" in tier_raw: txt += "+"
        
        lbl = QLabel(txt)
        lbl.setStyleSheet(f"""
            color: {color}; 
            border: 1px solid {color}; 
            background: rgba(0,0,0,0.2); 
            border-radius: 3px; 
            padding: 1px 4px;
            font-weight: bold;
            font-size: 11px;
            font-family: 'Microsoft YaHei UI';
        """)
        return lbl

    def _create_tags_row(self) -> QWidget:
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(4)
        
        tags = self.item_data.get("tags", [])
        if isinstance(tags, str): tags = [tags]
        
        # 只显示前3-4个标签，避免太长
        for t in tags[:4]:
            t = t.strip()
            if not t: continue
            lbl = QLabel(t)
            lbl.setStyleSheet("""
                background: rgba(152, 168, 254, 0.15);
                color: #98a8fe;
                border: 1px solid rgba(152, 168, 254, 0.3);
                border-radius: 3px;
                padding: 1px 6px;
                font-size: 10px;
                font-family: 'Microsoft YaHei UI';
            """)
            l.addWidget(lbl)
        
        l.addStretch()
        return w

    def _create_hero_avatar(self) -> QLabel:
        heroes = self.item_data.get("heroes", [])
        if not heroes or (isinstance(heroes, list) and "Common" in str(heroes[0])): return None
        
        hero_raw = heroes[0] if isinstance(heroes, list) else str(heroes)
        hero_name = hero_raw.split("/")[0] 
        
        label = QLabel()
        label.setFixedSize(32, 32)
        
        # Load logic simplified
        path = Path(f"assets/images/heroes/{hero_name}.webp")
        if path.exists():
             pix = QPixmap(str(path)).scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
             
             # Circular mask
             rounded = QPixmap(32, 32)
             rounded.fill(Qt.GlobalColor.transparent)
             painter = QPainter(rounded)
             painter.setRenderHint(QPainter.RenderHint.Antialiasing)
             path_draw = QPainterPath()
             path_draw.addEllipse(0, 0, 32, 32)
             painter.setClipPath(path_draw)
             painter.drawPixmap(0, 0, pix)
             painter.end()
             label.setPixmap(rounded)
             label.setToolTip(f"专属英雄: {hero_name}")
        return label

    def _load_image(self, label: QLabel, item_id: str, size: int):
        path = Path(f"assets/images/card/{item_id}.webp")
        if not path.exists():
            path = Path(f"assets/images/skill/{item_id}.webp")
            
        if path.exists():
            pix = QPixmap(str(path)).scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            # Rounded rect mask
            rounded = QPixmap(size, size)
            rounded.fill(Qt.GlobalColor.transparent)
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            p = QPainterPath()
            p.addRoundedRect(0, 0, size, size, 4, 4)
            painter.setClipPath(p)
            painter.drawPixmap(0, 0, pix)
            painter.end()
            
            label.setPixmap(rounded)
        else:
             label.setStyleSheet("background: #333; border-radius: 4px;")

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.details.setVisible(self.is_expanded)
        
        # Update styling
        scale = self.content_scale
        base_style = f"""
            #ItemDetailCard {{
                background: #2B2621;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-left: 0px solid transparent;
                border-radius: 6px;
            }}
            #ItemDetailCard:hover {{
                background: #322C28;
                border-left: 3px solid #ffcc00;
            }}
        """
        active_style = f"""
            #ItemDetailCard {{
                background: #322C28;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-left: 3px solid #ffcc00;
                border-radius: 6px;
            }}
        """
        self.setStyleSheet(active_style if self.is_expanded else base_style)
        
        # Find arrow and update
        for child in self.findChildren(QLabel):
            if child.text() in ["▴", "▾"]:
                child.setText("▴" if self.is_expanded else "▾")
                break
