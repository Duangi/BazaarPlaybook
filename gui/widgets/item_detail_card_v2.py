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
from utils.i18n import I18nManager
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
        
        # ✅ 初始化i18n管理器
        self.i18n = I18nManager()
        
        # ✅ 获取starting_tier用于设置边框颜色
        # starting_tier格式: "Bronze / 青铜", "Gold / 黄金" 等
        starting_tier_raw = self.item_data.get("starting_tier", "Bronze / 青铜")
        if "/" in starting_tier_raw:
            starting_tier_en = starting_tier_raw.split("/")[0].strip()
        else:
            starting_tier_en = starting_tier_raw.strip()
        
        self.starting_tier = starting_tier_en.lower()  # 转为小写用于查找
        self.tier_colors_map = {
            "bronze": "#cd7f32",
            "silver": "#c0c0c0",
            "gold": "#ffd700",
            "diamond": "#b9f2ff",
            "legendary": "#ff4500"
        }
        self.border_color = self.tier_colors_map.get(self.starting_tier, "#cd7f32")
        
        self.setObjectName("ItemDetailCard")
        self._update_style()
        
        # ✅ 关键修复：设置SizePolicy，防止卡片被垂直拉伸
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self._init_ui()
    
    def _update_style(self):
        """更新组件样式（边框颜色始终使用starting_tier）"""
        self.setStyleSheet(f"""
            #ItemDetailCard {{
                background: #2B2621;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-left: 3px solid {self.border_color};
                border-radius: 6px;
            }}
            #ItemDetailCard:hover {{
                background: #322C28;
                border-left: 3px solid {self.border_color};
            }}
        """)

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
        
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(12, 8, 12, 8)
        h_layout.setSpacing(12)
        
        # ✅ 左侧图标（根据卡牌尺寸自适应，不使用固定容器）
        # 根据卡牌尺寸计算实际图片大小（小:中:大 = 1:2:3）
        card_size = self.item_data.get("size", "medium / 中").split(" / ")[0].lower()
        if card_size == "small":
            actual_icon_size = 32  # 1单位
        elif card_size == "large":
            actual_icon_size = 96  # 3单位
        else:  # medium
            actual_icon_size = 64  # 2单位
        
        icon_label = QLabel()
        icon_label.setFixedSize(actual_icon_size, 64)  # 高度固定为64
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._load_image(icon_label, self.item_data.get("id"), actual_icon_size, 64)
        
        h_layout.addWidget(icon_label)
        
        # 中间信息（左侧）
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # 第一行：名称 + 品级
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        
        # 根据当前语言选择名称
        current_lang = self.i18n.get_language()
        if current_lang == "en_US":
            name = self.item_data.get("name", "Unknown")
        else:
            name_cn = self.item_data.get("name_cn", "")
            name_en = self.item_data.get("name", "Unknown")
            name = self.i18n.translate(name_cn, name_en) if name_cn else name_en
        
        name_label = QLabel(name)
        name_label.setStyleSheet("color: white; font-weight: bold; font-family: 'Microsoft YaHei UI'; font-size: 16px;")
        top_row.addWidget(name_label)
        
        tier_label = self._create_tier_label()
        if tier_label:
            top_row.addWidget(tier_label)
        
        top_row.addStretch()
        info_layout.addLayout(top_row)
        
        # 第二行：属性标签
        tags_row = self._create_tags_row()
        info_layout.addWidget(tags_row)
        
        info_layout.addStretch()
        h_layout.addLayout(info_layout, 1)
        
        # ✅ 右侧布局：英雄头像 + 箭头（独立列）
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        right_layout.setSpacing(4)
        
        # 英雄头像在顶部
        hero_avatar = self._create_hero_avatar()
        if hero_avatar:
            right_layout.addWidget(hero_avatar)
        
        # 箭头放到底部
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
        
        # ✅ 1. 冷却时间（支持分级显示）
        cooldown_tiers = self.item_data.get("cooldown_tiers")
        cooldown = self.item_data.get("cooldown")
        
        if cooldown_tiers or cooldown:
            cd_layout = QHBoxLayout()
            cd_layout.setSpacing(6)
            
            if cooldown_tiers and "/" in str(cooldown_tiers):
                # 显示分级冷却时间，用箭头连接
                tiers = str(cooldown_tiers).split("/")
                for i, tier_cd in enumerate(tiers):
                    cd_val = QLabel(tier_cd)
                    cd_val.setStyleSheet("color: #33CCFF; font-size: 20px; font-weight: bold; font-family: 'Microsoft YaHei UI';")
                    cd_layout.addWidget(cd_val)
                    
                    if i < len(tiers) - 1:
                        arrow = QLabel("→")
                        arrow.setStyleSheet("color: #666; font-size: 16px; padding: 0 4px;")
                        cd_layout.addWidget(arrow)
                
                cd_unit = QLabel(self.i18n.translate("秒", "s"))
                cd_unit.setStyleSheet("color: #33CCFF; font-size: 14px; padding-top: 4px; font-family: 'Microsoft YaHei UI';")
                cd_layout.addWidget(cd_unit)
            else:
                # 单一冷却时间
                cd_val = QLabel(str(cooldown))
                cd_val.setStyleSheet("color: #33CCFF; font-size: 24px; font-weight: bold; font-family: 'Microsoft YaHei UI';")
                cd_unit = QLabel(self.i18n.translate("秒", "s"))
                cd_unit.setStyleSheet("color: #33CCFF; font-size: 14px; padding-top: 8px; font-family: 'Microsoft YaHei UI';")
                cd_layout.addWidget(cd_val)
                cd_layout.addWidget(cd_unit)
            
            cd_layout.addStretch()
            layout.addLayout(cd_layout)
        
        # ✅ 2. 主动技能 (skills) 或技能描述 (descriptions)
        # 技能数据使用descriptions字段，物品数据使用skills字段
        descriptions = self.item_data.get("descriptions", [])
        skills = self.item_data.get("skills", [])
        
        if descriptions:
            # ✅ 技能描述格式: [{"en": "...", "cn": "..."}]
            current_lang = self.i18n.get_language()
            for desc in descriptions:
                if isinstance(desc, dict):
                    if current_lang == "en_US":
                        desc_text = desc.get("en", "")
                    else:
                        desc_cn = desc.get("cn", "")
                        desc_en = desc.get("en", "")
                        desc_text = self.i18n.translate(desc_cn, desc_en) if desc_cn else desc_en
                    
                    if desc_text:
                        skill_label = QLabel("🗡️ " + self._format_text(desc_text))
                        skill_label.setWordWrap(True)
                        skill_label.setStyleSheet("color: #ddd; font-size: 14px; font-family: 'Microsoft YaHei UI'; line-height: 1.6; padding: 4px 0;")
                        layout.addWidget(skill_label)
        elif skills:
            # ✅ 物品技能格式
            for skill in skills:
                skill_text = self._extract_text(skill)
                if skill_text:
                    skill_label = QLabel("🗡️ " + self._format_text(skill_text))
                    skill_label.setWordWrap(True)
                    skill_label.setStyleSheet("color: #ddd; font-size: 14px; font-family: 'Microsoft YaHei UI'; line-height: 1.6; padding: 4px 0;")
                    layout.addWidget(skill_label)
        
        # ✅ 3. 被动技能 (skills_passive)
        skills_passive = self.item_data.get("skills_passive", [])
        if skills_passive:
            for skill in skills_passive:
                skill_text = self._extract_text(skill)
                if skill_text:
                    skill_label = QLabel("⚙️ " + self._format_text(skill_text))
                    skill_label.setWordWrap(True)
                    skill_label.setStyleSheet("color: #ccc; font-size: 13px; font-family: 'Microsoft YaHei UI'; line-height: 1.6; padding: 4px 0; font-style: italic;")
                    layout.addWidget(skill_label)
        
        # ✅ 4. 任务 (quests)
        # 新格式: [{"en_target": "...", "cn_target": "...", "en_reward": "...", "cn_reward": "..."}]
        quests = self.item_data.get("quests")
        if quests:
            current_lang = self.i18n.get_language()
            
            if isinstance(quests, list):
                for i, quest in enumerate(quests, 1):
                    if isinstance(quest, dict):
                        # 新格式：包含 target 和 reward
                        if current_lang == "en_US":
                            target = quest.get("en_target", "")
                            reward = quest.get("en_reward", "")
                        else:
                            target_cn = quest.get("cn_target", "")
                            target_en = quest.get("en_target", "")
                            reward_cn = quest.get("cn_reward", "")
                            reward_en = quest.get("en_reward", "")
                            target = self.i18n.translate(target_cn, target_en) if target_cn else target_en
                            reward = self.i18n.translate(reward_cn, reward_en) if reward_cn else reward_en
                        
                        if target or reward:
                            # 显示任务序号
                            quest_header = QLabel(f"📜 {self.i18n.translate('任务', 'Quest')} {i}:")
                            quest_header.setWordWrap(True)
                            quest_header.setStyleSheet("color: #9098fe; font-size: 13px; font-family: 'Microsoft YaHei UI'; font-weight: bold; padding: 4px 0 2px 0;")
                            layout.addWidget(quest_header)
                            
                            # 显示目标
                            if target:
                                target_label = QLabel(f"  → {self._format_text(target)}")
                                target_label.setWordWrap(True)
                                target_label.setStyleSheet("color: #aaa; font-size: 12px; font-family: 'Microsoft YaHei UI'; line-height: 1.4; padding: 2px 0 2px 12px;")
                                layout.addWidget(target_label)
                            
                            # 显示奖励
                            if reward:
                                reward_label = QLabel(f"  ✨ {self._format_text(reward)}")
                                reward_label.setWordWrap(True)
                                reward_label.setStyleSheet("color: #ffcc00; font-size: 12px; font-family: 'Microsoft YaHei UI'; line-height: 1.4; padding: 2px 0 4px 12px;")
                                layout.addWidget(reward_label)
                    else:
                        # 旧格式：直接是文本
                        quest_text = self._extract_text(quest)
                        if quest_text:
                            quest_label = QLabel("📜 " + self._format_text(quest_text))
                            quest_label.setWordWrap(True)
                            quest_label.setStyleSheet("color: #9098fe; font-size: 13px; font-family: 'Microsoft YaHei UI'; line-height: 1.6; padding: 4px 0;")
                            layout.addWidget(quest_label)
            elif isinstance(quests, dict):
                # 单个任务对象
                if current_lang == "en_US":
                    target = quests.get("en_target", "")
                    reward = quests.get("en_reward", "")
                else:
                    target_cn = quests.get("cn_target", "")
                    target_en = quests.get("en_target", "")
                    reward_cn = quests.get("cn_reward", "")
                    reward_en = quests.get("en_reward", "")
                    target = self.i18n.translate(target_cn, target_en) if target_cn else target_en
                    reward = self.i18n.translate(reward_cn, reward_en) if reward_cn else reward_en
                
                if target or reward:
                    quest_header = QLabel(f"📜 {self.i18n.translate('任务', 'Quest')}:")
                    quest_header.setWordWrap(True)
                    quest_header.setStyleSheet("color: #9098fe; font-size: 13px; font-family: 'Microsoft YaHei UI'; font-weight: bold; padding: 4px 0 2px 0;")
                    layout.addWidget(quest_header)
                    
                    if target:
                        target_label = QLabel(f"  → {self._format_text(target)}")
                        target_label.setWordWrap(True)
                        target_label.setStyleSheet("color: #aaa; font-size: 12px; font-family: 'Microsoft YaHei UI'; line-height: 1.4; padding: 2px 0 2px 12px;")
                        layout.addWidget(target_label)
                    
                    if reward:
                        reward_label = QLabel(f"  ✨ {self._format_text(reward)}")
                        reward_label.setWordWrap(True)
                        reward_label.setStyleSheet("color: #ffcc00; font-size: 12px; font-family: 'Microsoft YaHei UI'; line-height: 1.4; padding: 2px 0 4px 12px;")
                        layout.addWidget(reward_label)
                else:
                    # 旧格式
                    quest_text = self._extract_text(quests)
                    if quest_text:
                        quest_label = QLabel("📜 " + self._format_text(quest_text))
                        quest_label.setWordWrap(True)
                        quest_label.setStyleSheet("color: #9098fe; font-size: 13px; font-family: 'Microsoft YaHei UI'; line-height: 1.6; padding: 4px 0;")
                        layout.addWidget(quest_label)
        
        # ✅ 5. 附魔效果 (enchantments)
        enchantments = self.item_data.get("enchantments", {})
        if enchantments and isinstance(enchantments, dict):
            for ench_key, ench_data in enchantments.items():
                if isinstance(ench_data, dict):
                    # 根据当前语言选择名称和效果文本
                    current_lang = self.i18n.get_language()
                    if current_lang == "en_US":
                        name = ench_data.get("name_en", ench_key)
                        effect = ench_data.get("effect_en", "")
                    else:
                        name_cn = ench_data.get("name_cn", ench_key)
                        name_en = ench_data.get("name_en", ench_key)
                        effect_cn = ench_data.get("effect_cn", "")
                        effect_en = ench_data.get("effect_en", "")
                        name = self.i18n.translate(name_cn, name_en) if name_cn else name_en
                        effect = self.i18n.translate(effect_cn, effect_en) if effect_cn else effect_en
                    
                    # 根据附魔类型设置颜色
                    enchant_colors = {
                        "Golden": "#f59e0b", "Heavy": "#5c7cfa", "Icy": "#22b8cf",
                        "Turbo": "#00ecc3", "Shielded": "#f4cf20", "Restorative": "#8eea31",
                        "Toxic": "#0ebe4f", "Fiery": "#ff9f45", "Shiny": "#98a8fe",
                        "Deadly": "#f5503d", "Radiant": "#98a8fe", "Obsidian": "#9d4a6f"
                    }
                    color = enchant_colors.get(ench_key, "#999")
                    
                    row = self._create_effect_row(name, effect, color)
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
        """从可能是dict/str的对象提取文本（根据当前语言）"""
        if isinstance(obj, dict):
            current_lang = self.i18n.get_language()
            if current_lang == "en_US":
                return obj.get("en", "")
            else:
                # 简体/繁体中文
                cn_text = obj.get("cn", "")
                en_text = obj.get("en", "")
                return self.i18n.translate(cn_text, en_text) if cn_text else en_text
        return str(obj) if obj else ""

    def _create_tier_label(self) -> QLabel:
        """创建品级标签
        
        规则：
        - 青铜 → 青铜+
        - 白银 → 白银+
        - 黄金 → 黄金+
        - 钻石 → 钻石（不加+）
        - 传说 → 传说（不加+）
        """
        # ✅ 使用 starting_tier，格式如 "Gold / 黄金" 或 "Bronze / 青铜"
        tier_raw = self.item_data.get("starting_tier", "Bronze / 青铜")
        if not tier_raw:
            tier_raw = "Bronze / 青铜"
        
        # 解析 "English / 中文" 格式
        if "/" in tier_raw:
            parts = tier_raw.split("/")
            tier_en = parts[0].strip()
            tier_cn = parts[1].strip() if len(parts) > 1 else tier_en
        else:
            tier_en = tier_raw.strip()
            tier_cn = tier_raw.strip()
        
        # 品级映射表
        tier_colors = {
            "bronze": ("#cd7f32", "青铜+", "Bronze+"),
            "silver": ("#c0c0c0", "白银+", "Silver+"),
            "gold": ("#ffd700", "黄金+", "Gold+"), 
            "diamond": ("#b9f2ff", "钻石", "Diamond"),  # 钻石不加+
            "legendary": ("#ff4500", "传说", "Legendary")  # 传说不加+
        }
        
        # 根据英文名称获取配置
        tier_key = tier_en.lower()
        color, display_cn, display_en = tier_colors.get(tier_key, ("#cd7f32", "青铜+", "Bronze+"))
        
        # 根据当前语言选择显示文本
        current_lang = self.i18n.get_language()
        if current_lang == "en_US":
            display_text = display_en
        else:
            # 简体/繁体中文
            display_text = self.i18n.translate(display_cn, display_en)
        
        lbl = QLabel(display_text)
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
        """创建标签行，支持多语言"""
        w = QWidget()
        w.setFixedHeight(20)  # ✅ 固定标签行高度，避免被拉伸
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)  # ✅ 顶部对齐
        
        tags = self.item_data.get("tags", "")
        if not tags:
            layout.addStretch()
            return w
        
        # 解析标签字符串 "Tag1 / 标签1 | Tag2 / 标签2"
        tag_list = [t.strip() for t in tags.split("|")] if isinstance(tags, str) else tags
        
        # 只显示前3-4个标签，避免太长
        for tag_text in tag_list[:4]:
            if not tag_text:
                continue
            
            # 解析 "English / 中文" 格式
            if "/" in tag_text:
                parts = tag_text.split("/")
                en_text = parts[0].strip()
                cn_text = parts[1].strip() if len(parts) > 1 else en_text
            else:
                en_text = tag_text.strip()
                cn_text = tag_text.strip()
            
            # 根据当前语言选择显示文本
            current_lang = self.i18n.get_language()
            if current_lang == "en_US":
                display_text = en_text
            else:
                # 简体中文和繁体中文都显示中文
                display_text = self.i18n.translate(cn_text, en_text)
            
            lbl = QLabel(display_text)
            lbl.setStyleSheet("""
                background: rgba(152, 168, 254, 0.15);
                color: #98a8fe;
                border: 1px solid rgba(152, 168, 254, 0.3);
                border-radius: 3px;
                padding: 1px 6px;
                font-size: 10px;
                font-family: 'Microsoft YaHei UI';
            """)
            layout.addWidget(lbl)
        
        layout.addStretch()
        return w

    def _create_hero_avatar(self) -> QWidget:
        """创建英雄头像（通用英雄不显示标签）
        
        Returns:
            如果是专属英雄，返回带圆框的圆形头像；如果是通用，返回None（不显示）
        """
        heroes = self.item_data.get("heroes", "")
        if not heroes:
            return None
        
        # 解析 "Pygmalien / 皮格马利翁" 或 "Common / 通用" 格式
        hero_raw = heroes[0] if isinstance(heroes, list) else str(heroes)
        if "/" in hero_raw:
            hero_en = hero_raw.split("/")[0].strip()
            hero_cn = hero_raw.split("/")[1].strip() if "/" in hero_raw else hero_en
        else:
            hero_en = hero_raw.strip()
            hero_cn = hero_raw.strip()
        
        # ✅ 如果是通用，不显示任何标签（返回None）
        if hero_en.lower() == "common":
            return None
        
        # ✅ 否则返回带圆框的圆形英雄头像
        container = QWidget()
        container.setFixedSize(36, 36)  # 外层容器稍大，留出边框空间
        
        label = QLabel(container)
        label.setFixedSize(32, 32)
        label.move(2, 2)  # 居中放置
        
        # 加载英雄头像
        path = Path(f"assets/images/heroes/{hero_en}.webp")
        if path.exists():
            pix = QPixmap(str(path)).scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            # 圆形遮罩
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
            
            # 根据语言设置提示文本
            current_lang = self.i18n.get_language()
            if current_lang == "en_US":
                label.setToolTip(f"Exclusive Hero: {hero_en}")
            else:
                tooltip_text = self.i18n.translate(f"专属英雄: {hero_cn}", f"Exclusive Hero: {hero_en}")
                label.setToolTip(tooltip_text)
        
        # ✅ 添加圆形边框到容器
        container.setStyleSheet("""
            QWidget {
                background: transparent;
                border: 2px solid rgba(212, 175, 55, 0.6);
                border-radius: 18px;
            }
        """)
        
        return container

    def _load_image(self, label: QLabel, item_id: str, width: int, height: int):
        """加载并显示物品/技能图片
        
        Args:
            label: 目标QLabel
            item_id: 物品/技能ID
            width: 图片宽度
            height: 图片高度
        """
        # ✅ 优先使用art_key字段（技能专用）
        art_key = self.item_data.get("art_key", "")
        path = None
        
        if art_key:
            # 从art_key提取文件名
            # "Assets/TheBazaar/Art/UI/Skills/Stelle/Icon_Skill_STE_ThrillOfTheFlight.png"
            # → "Icon_Skill_STE_ThrillOfTheFlight.png"
            filename = art_key.split("/")[-1] if "/" in art_key else art_key
            # 处理后缀：去掉.png后缀，添加.webp
            if filename.endswith(".png"):
                filename = filename[:-4] + ".webp"
            elif not filename.endswith(".webp"):
                # 如果没有任何后缀，添加.webp
                filename = filename + ".webp"
            
            # 优先在skill目录查找
            skill_path = Path(f"assets/images/skill/{filename}")
            if skill_path.exists():
                path = skill_path
            else:
                # 也尝试使用item_id
                skill_path_id = Path(f"assets/images/skill/{item_id}.webp")
                if skill_path_id.exists():
                    path = skill_path_id
        
        # 如果没有art_key或找不到，使用item_id在card目录查找
        if not path:
            card_path = Path(f"assets/images/card/{item_id}.webp")
            if card_path.exists():
                path = card_path
            else:
                # 最后尝试skill目录
                skill_path = Path(f"assets/images/skill/{item_id}.webp")
                if skill_path.exists():
                    path = skill_path
            
        if path and path.exists():
            # ✅ 先按宽度缩放，如果高度不足则拉伸至目标高度
            original_pix = QPixmap(str(path))
            
            # 先按宽度等比缩放
            scaled_pix = original_pix.scaled(
                width, 99999,  # 先按宽度缩放，高度不限
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            
            # 如果缩放后高度小于目标高度，则在高度上拉伸
            if scaled_pix.height() < height:
                scaled_pix = scaled_pix.scaled(
                    width, height,
                    Qt.AspectRatioMode.IgnoreAspectRatio,  # 忽略比例，拉伸至目标尺寸
                    Qt.TransformationMode.SmoothTransformation
                )
            
            pix = scaled_pix
            
            # 创建圆角矩形遮罩
            rounded = QPixmap(width, height)
            rounded.fill(Qt.GlobalColor.transparent)
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            p = QPainterPath()
            p.addRoundedRect(0, 0, width, height, 4, 4)
            painter.setClipPath(p)
            
            # 居中绘制图片
            x_offset = (width - pix.width()) // 2
            y_offset = (height - pix.height()) // 2
            painter.drawPixmap(x_offset, y_offset, pix)
            painter.end()
            
            label.setPixmap(rounded)
        else:
            # 如果图片不存在，显示占位符
            label.setStyleSheet("background: #333; border-radius: 4px;")
            label.setText("?")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("background: #333; border-radius: 4px; color: #666; font-size: 24px;")

    def toggle_expand(self):
        """切换展开/折叠状态"""
        self.is_expanded = not self.is_expanded
        self.details.setVisible(self.is_expanded)
        
        # ✅ 始终保持边框颜色不变，仅更新背景色
        if self.is_expanded:
            self.setStyleSheet(f"""
                #ItemDetailCard {{
                    background: #322C28;
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    border-left: 3px solid {self.border_color};
                    border-radius: 6px;
                }}
            """)
        else:
            self._update_style()
        
        # Find arrow and update
        for child in self.findChildren(QLabel):
            if child.text() in ["▴", "▾"]:
                child.setText("▴" if self.is_expanded else "▾")
                break
    
    def update_language(self):
        """更新语言显示"""
        # 重新创建UI以应用新语言
        # 清空现有内容
        while self.layout().count():
            item = self.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 重新初始化UI
        self._init_ui()
