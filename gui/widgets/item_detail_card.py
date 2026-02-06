"""
物品详情卡片组件 (Item Detail Card)
完全参考 App.tsx 的实现，可展开/折叠的卡片
支持多等级切换和详细信息显示
"""
from typing import Dict, List
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QButtonGroup)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QFont
from utils.i18n import get_i18n
from utils.image_loader import ImageLoader, CardSize
import os
import json


class ItemDetailCard(QFrame):
    """
    物品详情卡片（技能或卡牌）
    - 点击卡片展开/折叠
    - 显示所有等级信息
    - 支持切换当前等级
    """
    
    tier_changed = Signal(str)  # 当前等级改变信号
    
    def __init__(self, item_id: str = None, item_type: str = "skill", 
                 current_tier: str = "bronze", parent=None, default_expanded: bool = False,
                 enable_tier_click: bool = False, content_scale: float = 1.0, item_data: Dict = None):
        super().__init__(parent)
        self.item_id = item_id
        self.item_type = item_type
        self.current_tier = current_tier.lower()
        self.i18n = get_i18n()
        self.content_scale = content_scale  # ✅ 内容缩放比例
        # 初始展开状态（可由调用方覆盖）
        self.is_expanded = False
        self._default_expanded = bool(default_expanded)
        self.show_all_tiers = False  # 是否显示所有等级
        self.enable_tier_click = enable_tier_click  # 是否允许点击详情区域切换等级
        
        # 加载数据（如果提供了item_data则直接使用，否则从数据库加载）
        if item_data:
            self.item_data = item_data
            if not self.item_id and item_data.get("id"):
                self.item_id = item_data["id"]
        else:
            self.item_data = self._load_item_data()
        
        if not self.item_data:
            return
        
        self._init_ui()
        # 如果被要求默认展开，触发展开行为（safe）
        try:
            if self._default_expanded and not self.is_expanded:
                self.toggle_expand()
        except Exception:
            pass
    
    def _load_item_data(self) -> Dict:
        """从数据库加载物品数据"""
        try:
            db_path = "assets/json/skills_db.json" if self.item_type == "skill" else "assets/json/items_db.json"
            
            if os.path.exists(db_path):
                with open(db_path, 'r', encoding='utf-8') as f:
                    db = json.load(f)
                    for item in db:
                        if item.get("id") == self.item_id:
                            return item
        except Exception as e:
            print(f"Error loading {self.item_type} data: {e}")
        return {}
    
    def _get_enchantment_data(self) -> Dict:
        """获取当前物品的附魔数据"""
        # ✅ 直接从当前物品数据中获取附魔定义
        return self.item_data.get("enchantments", {})
    
    def _init_ui(self):
        """初始化UI - 完全参考 App.tsx 的结构"""
        self.setObjectName("ItemDetailCard")
        self.setProperty("class", "item-card-container")
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. 卡片头部（始终可见，点击展开/折叠）
        self.card_header = self._create_card_header()
        main_layout.addWidget(self.card_header)
        
        # 2. 详情区域（可展开/折叠）
        self.details_widget = self._create_details_widget()
        self.details_widget.setMaximumHeight(0)  # 初始折叠
        self.details_widget.setVisible(False)
        main_layout.addWidget(self.details_widget)
        
        self._setup_style()
    
    def _create_card_header(self) -> QWidget:
        """创建卡片头部 - 参考 .item-card"""
        header = QFrame()
        header.setObjectName("ItemCardHeader")
        header.setCursor(Qt.CursorShape.PointingHandCursor)
        header.mousePressEvent = lambda e: self.toggle_expand()
        
        # ✅ 应用缩放比例
        scale = self.content_scale
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(int(10 * scale), int(6 * scale), int(10 * scale), int(6 * scale))
        layout.setSpacing(int(10 * scale))
        
        # 左侧：图标（缩小一点）
        icon_size = int(42 * scale)  # 应用缩放
        size_class = self._get_size_class()
        
        icon_container = QFrame()
        icon_container.setObjectName("ImageBox")
        icon_container.setProperty("size_class", size_class)
        
        if size_class == "small":
            icon_container.setFixedSize(int(icon_size * 0.5), icon_size)
        elif size_class == "large":
            icon_container.setFixedSize(int(icon_size * 1.5), icon_size)
        else:
            icon_container.setFixedSize(icon_size, icon_size)
        
        icon_label = QLabel(icon_container)
        pixmap = self._load_icon(icon_size)
        icon_label.setPixmap(pixmap)
        icon_label.setScaledContents(True)
        icon_label.setGeometry(0, 0, icon_container.width(), icon_container.height())
        
        layout.addWidget(icon_container)
        
        # 中间：名称和标签
        center_layout = QVBoxLayout()
        center_layout.setSpacing(int(2 * scale))  # 应用缩放
        
        # 名称行
        name_layout = QHBoxLayout()
        name_layout.setSpacing(int(6 * scale))  # 应用缩放
        
        lang = self.i18n.get_language()
        name = self.item_data.get("name_cn" if lang != "en_US" else "name_en", "Unknown")
        if lang == "zh_TW":
            name = self.i18n.to_traditional(name)
        
        # ✅ 如果有附魔，添加附魔名称前缀
        enchantment_key = self.item_data.get("enchantment", "")
        if enchantment_key:
            enchantments_db = self._get_enchantment_data()
            if enchantment_key in enchantments_db:
                enchant_data = enchantments_db[enchantment_key]
                enchant_name = enchant_data.get("name_cn", enchantment_key)
                if lang == "zh_TW":
                    enchant_name = self.i18n.to_traditional(enchant_name)
                elif lang == "en_US":
                    enchant_name = enchantment_key  # 英文直接用key
                name = f"{enchant_name} {name}"
        
        name_label = QLabel(name)
        name_label.setObjectName("NameCn")
        # ✅ 应用缩放到字体
        name_label.setStyleSheet(f"color: #fff; font-size: {int(11 * scale)}pt; font-weight: 700;")
        name_layout.addWidget(name_label)
        
        # 等级标签（根据 available_tiers 或 starting_tier）
        tier_display = self._get_tier_display_name()
        tier_label = QLabel(tier_display)
        tier_label.setObjectName("TierLabel")
        tier_label.setProperty("tier_class", self.current_tier)
        tier_label.setFixedHeight(int(18 * scale))  # ✅ 固定高度，不随内容变化
        name_layout.addWidget(tier_label)
        name_layout.addStretch()
        
        center_layout.addLayout(name_layout)
        
        # 标签行（解析 "英文 / 中文 | 英文 / 中文" 格式）
        # ✅ 创建固定高度的标签容器
        tags_container = QWidget()
        tags_container.setFixedHeight(int(20 * scale))  # 固定高度，不随内容变化
        
        tags_layout = QHBoxLayout(tags_container)
        tags_layout.setContentsMargins(0, 0, 0, 0)
        tags_layout.setSpacing(int(4 * scale))
        
        # 解析tags字符串
        tags_str = self.item_data.get("tags", "")
        tag_pairs = []
        if tags_str:
            # 按 | 分割成多个tag对
            for tag_pair in tags_str.split("|"):
                tag_pair = tag_pair.strip()
                if "/" in tag_pair:
                    # 分割英文和中文
                    parts = tag_pair.split("/")
                    if len(parts) >= 2:
                        en_tag = parts[0].strip()
                        cn_tag = parts[1].strip()
                        tag_pairs.append((en_tag, cn_tag))
        
        # 显示前3个tag（增加到3个）
        for en_tag, cn_tag in tag_pairs[:3]:
            # 根据语言选择显示
            if lang == "en_US":
                display_tag = en_tag
            elif lang == "zh_TW":
                display_tag = self.i18n.to_traditional(cn_tag)
            else:
                display_tag = cn_tag
            
            tag_badge = QLabel(display_tag)
            tag_badge.setObjectName("TagBadge")
            # ✅ 移除内联样式，使用样式表中的定义
            tags_layout.addWidget(tag_badge)
        tags_layout.addStretch()
        
        center_layout.addWidget(tags_container)  # ✅ 添加容器而不是布局
        
        layout.addLayout(center_layout, 1)
        
        # 右侧：展开箭头
        self.expand_chevron = QLabel("▾")
        # ✅ 应用缩放到箭头字体
        self.expand_chevron.setStyleSheet(f"color: rgba(255, 255, 255, 0.35); font-size: {int(12 * scale)}pt; padding-right: {int(4 * scale)}px;")
        layout.addWidget(self.expand_chevron)
        
        return header
    
    def _create_details_widget(self) -> QWidget:
        """创建详情区域 - 参考 .item-details-v2"""
        details = QFrame()
        details.setObjectName("ItemDetailsV2")
        
        # ✅ 应用缩放比例
        scale = self.content_scale
        
        layout = QVBoxLayout(details)
        layout.setContentsMargins(int(12 * scale), int(12 * scale), int(12 * scale), int(12 * scale))
        layout.setSpacing(int(10 * scale))
        
        # 技能描述区域
        self.description_container = QFrame()
        desc_layout = QVBoxLayout(self.description_container)
        desc_layout.setContentsMargins(0, 0, 0, 0)
        desc_layout.setSpacing(int(6 * scale))
        
        self._update_descriptions(desc_layout)
        
        layout.addWidget(self.description_container)
        # 不添加底部弹性空间，让内容紧凑
        
        return details
    
    def _toggle_tier_display(self):
        """切换等级显示模式"""
        # 检查是否有多个等级
        available_tiers = self.item_data.get("available_tiers", "Bronze")
        tiers = [t.strip().lower() for t in available_tiers.replace("/", ",").split(",") if t.strip()]
        
        if len(tiers) <= 1:
            return  # 只有一个等级，不切换
        
        if not hasattr(self, 'available_tiers'):
            self.available_tiers = tiers
        
        # 切换显示模式
        self.show_all_tiers = not self.show_all_tiers
        self._update_descriptions(self.description_container.layout())
        
        # 如果是弹窗窗口，更新内容后重新提升到最上层
        if self.windowFlags() & Qt.Tool:
            try:
                self.raise_()
                self.activateWindow()
            except Exception:
                pass
    
    def _update_descriptions(self, parent_layout: QVBoxLayout):
        """更新描述文本 - 根据类型显示 descriptions 或 skills/skills_passive"""
        # 清空旧内容
        while parent_layout.count():
            item = parent_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        lang = self.i18n.get_language()
        
        # ✅ 应用缩放比例到字体和边距
        scale = self.content_scale
        
        # 优先显示 descriptions（技能数据）
        descriptions = self.item_data.get("descriptions", [])
        if descriptions:
            for desc_obj in descriptions:
                desc_text = desc_obj.get("cn" if lang != "en_US" else "en", "")
                if lang == "zh_TW":
                    desc_text = self.i18n.to_traditional(desc_text)
                
                if desc_text:
                    # 处理等级数值显示
                    desc_text = self._process_tier_values(desc_text)
                    
                    desc_label = QLabel(f"⚡ {desc_text}")
                    desc_label.setWordWrap(True)
                    desc_label.setStyleSheet(f"""
                        color: #ffd666;
                        font-size: {int(9 * scale)}pt;
                        line-height: 1.4;
                        background: rgba(255, 214, 102, 0.08);
                        border: 1px solid rgba(255, 214, 102, 0.15);
                        border-radius: {int(6 * scale)}px;
                        padding: {int(8 * scale)}px {int(10 * scale)}px;
                    """)
                    
                    # 如果启用了等级点击切换，为每个描述框添加点击事件
                    if self.enable_tier_click:
                        desc_label.setCursor(Qt.CursorShape.PointingHandCursor)
                        # 使用默认参数捕获当前 label，避免闭包问题
                        desc_label.mousePressEvent = lambda event, lbl=desc_label: self._toggle_tier_display()
                    
                    parent_layout.addWidget(desc_label)
            return
        
        # 如果没有 descriptions，则显示 skills 和 skills_passive（物品数据）
        # 1. 显示主动技能 (skills)
        skills = self.item_data.get("skills", [])
        if skills:
            for skill_obj in skills:
                skill_text = skill_obj.get("cn" if lang != "en_US" else "en", "")
                if lang == "zh_TW":
                    skill_text = self.i18n.to_traditional(skill_text)
                
                if skill_text:
                    # 处理等级数值显示
                    skill_text = self._process_tier_values(skill_text)
                    
                    skill_label = QLabel(f"⚡ {skill_text}")
                    skill_label.setWordWrap(True)
                    skill_label.setStyleSheet(f"""
                        color: #ffd666;
                        font-size: {int(9 * scale)}pt;
                        line-height: 1.4;
                        background: rgba(255, 214, 102, 0.08);
                        border: 1px solid rgba(255, 214, 102, 0.15);
                        border-radius: {int(6 * scale)}px;
                        padding: {int(8 * scale)}px {int(10 * scale)}px;
                    """)
                    
                    # 如果启用了等级点击切换，为每个技能框添加点击事件
                    if self.enable_tier_click:
                        skill_label.setCursor(Qt.CursorShape.PointingHandCursor)
                        # 使用默认参数捕获当前 label，避免闭包问题
                        skill_label.mousePressEvent = lambda event, lbl=skill_label: self._toggle_tier_display()
                    
                    parent_layout.addWidget(skill_label)
        
        # 2. 显示被动技能 (skills_passive)
        skills_passive = self.item_data.get("skills_passive", [])
        if skills_passive:
            for passive_obj in skills_passive:
                passive_text = passive_obj.get("cn" if lang != "en_US" else "en", "")
                if lang == "zh_TW":
                    passive_text = self.i18n.to_traditional(passive_text)
                
                if passive_text:
                    # 处理等级数值显示
                    passive_text = self._process_tier_values(passive_text)
                    
                    passive_label = QLabel(f"🛡 {passive_text}")
                    passive_label.setWordWrap(True)
                    passive_label.setStyleSheet(f"""
                        color: #95de64;
                        font-size: {int(9 * scale)}pt;
                        line-height: 1.4;
                        background: rgba(149, 222, 100, 0.08);
                        border: 1px solid rgba(149, 222, 100, 0.15);
                        border-radius: {int(6 * scale)}px;
                        padding: {int(8 * scale)}px {int(10 * scale)}px;
                    """)
                    
                    # 如果启用了等级点击切换，为每个被动技能框添加点击事件
                    if self.enable_tier_click:
                        passive_label.setCursor(Qt.CursorShape.PointingHandCursor)
                        # 使用默认参数捕获当前 label，避免闭包问题
                        passive_label.mousePressEvent = lambda event, lbl=passive_label: self._toggle_tier_display()
                    
                    parent_layout.addWidget(passive_label)
        
        # 3. ✅ 显示附魔效果 (enchantment)
        enchantment_key = self.item_data.get("enchantment", "")
        if enchantment_key:
            enchantments_db = self._get_enchantment_data()
            if enchantment_key in enchantments_db:
                enchant_data = enchantments_db[enchantment_key]
                enchant_effect = enchant_data.get("effect_cn" if lang != "en_US" else "effect_en", "")
                if lang == "zh_TW":
                    enchant_effect = self.i18n.to_traditional(enchant_effect)
                
                if enchant_effect:
                    enchant_label = QLabel(f"✨ {enchant_effect}")
                    enchant_label.setWordWrap(True)
                    enchant_label.setStyleSheet(f"""
                        color: #d4b106;
                        font-size: {int(9 * scale)}pt;
                        line-height: 1.4;
                        background: rgba(212, 177, 6, 0.08);
                        border: 1px solid rgba(212, 177, 6, 0.15);
                        border-radius: {int(6 * scale)}px;
                        padding: {int(8 * scale)}px {int(10 * scale)}px;
                    """)
                    
                    # 如果启用了等级点击切换，为附魔框也添加点击事件
                    if self.enable_tier_click:
                        enchant_label.setCursor(Qt.CursorShape.PointingHandCursor)
                        enchant_label.mousePressEvent = lambda event, lbl=enchant_label: self._toggle_tier_display()
                    
                    parent_layout.addWidget(enchant_label)
    
    def _process_tier_values(self, text: str) -> str:
        """
        处理文本中的等级数值显示
        例如：将 "4/6" 根据当前等级和显示模式进行过滤
        """
        import re
        
        # 查找所有类似 "数字/数字/数字" 的模式
        def replace_values(match):
            values_str = match.group(0)
            values = values_str.split('/')
            
            if self.show_all_tiers:
                # 显示所有等级：保持原样
                return values_str
            else:
                # 只显示当前等级对应的数值
                if not hasattr(self, 'available_tiers') or not self.available_tiers:
                    return values[0] if values else values_str
                
                # 找到当前等级在可用等级列表中的索引
                try:
                    tier_index = self.available_tiers.index(self.current_tier)
                    if tier_index < len(values):
                        return values[tier_index]
                except (ValueError, IndexError):
                    pass
                
                # 默认返回第一个值
                return values[0] if values else values_str
        
        # 匹配数字/数字模式（可能有多组）
        result = re.sub(r'\d+(?:/\d+)+', replace_values, text)
        return result
    
    def _on_tier_changed(self, tier: str):
        """等级切换"""
        self.current_tier = tier
        self._update_descriptions(self.description_container.layout())
        self.tier_changed.emit(tier)
    
    def toggle_expand(self):
        """切换展开/折叠状态"""
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            self.setProperty("class", "item-card-container expanded")
            self.expand_chevron.setText("▴")
            self.details_widget.setVisible(True)
            self.details_widget.setMaximumHeight(16777215)
        else:
            self.setProperty("class", "item-card-container")
            self.expand_chevron.setText("▾")
            self.details_widget.setMaximumHeight(0)
            self.details_widget.setVisible(False)
        
        self.style().unpolish(self)
        self.style().polish(self)
    
    def _get_size_class(self) -> str:
        """获取尺寸类别"""
        if self.item_type == "item":
            size_str = self.item_data.get("size", "Medium / 中型")
            size_en = size_str.split("/")[0].strip().lower()
            if "small" in size_en:
                return "small"
            elif "large" in size_en:
                return "large"
        return "medium"
    
    def _load_icon(self, size: int) -> QPixmap:
        """加载图标"""
        if self.item_type == "skill":
            art_key = self.item_data.get("art_key", "")
            if art_key:
                filename = os.path.basename(art_key)
                skill_filename = os.path.splitext(filename)[0]
            else:
                skill_filename = self.item_id
            return ImageLoader.load_skill_image(skill_filename, size=size, with_border=True)
        else:
            size_class = self._get_size_class()
            card_size = CardSize.SMALL if size_class == "small" else (CardSize.LARGE if size_class == "large" else CardSize.MEDIUM)
            return ImageLoader.load_card_image(self.item_id, card_size, size, with_border=True)
    
    def _get_tier_display_name(self) -> str:
        """获取等级显示名称"""
        lang = self.i18n.get_language()
        tier_names = {
            "bronze": "青铜+",
            "silver": "白银+",
            "gold": "黄金+",
            "diamond": "钻石+"
        }
        
        if lang == "en_US":
            return self.current_tier.title() + "+"
        elif lang == "zh_TW":
            return self.i18n.to_traditional(tier_names.get(self.current_tier, "青铜+"))
        return tier_names.get(self.current_tier, "青铜+")
    
    def _get_tier_button_style(self) -> str:
        """获取等级按钮样式（已废弃，由 _update_tier_button_text 处理）"""
        return ""
    
    def _setup_style(self):
        """设置样式 - 完全参考 App.css，根据等级设置边框颜色"""
        # 等级颜色
        tier_colors = {
            "bronze": "#CD7F32",
            "silver": "#C0C0C0",
            "gold": "#FFD700",
            "diamond": "#B9F2FF"
        }
        
        border_color = tier_colors.get(self.current_tier, "#CD7F32")
        
        self.setStyleSheet(f"""
            #ItemDetailCard {{
                margin-bottom: 8px;
                background: rgba(20, 20, 22, 0.45);
                border-radius: 8px;
                border: 1px solid {border_color};
            }}
            #ItemDetailCard:hover {{
                background: rgba(30, 30, 32, 0.55);
                border-color: {border_color};
            }}
            #ItemDetailCard[class="item-card-container expanded"] {{
                background: rgba(12, 12, 14, 0.95);
                border-color: {border_color};
            }}
            #ItemCardHeader {{
                background: rgba(30, 30, 32, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.04);
                border-radius: 8px;
            }}
            #ItemCardHeader:hover {{
                background: rgba(40, 40, 44, 0.68);
            }}
            #ImageBox {{
                background: rgba(0, 0, 0, 0.35);
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.06);
            }}
            #TierLabel {{
                font-size: 9pt;
                font-weight: 800;
                padding: 1px 4px;
                border-radius: 3px;
                background: rgba(255, 255, 255, 0.08);
                color: rgba(255, 255, 255, 0.5);
            }}
            #TierLabel[tier_class="bronze"] {{ color: #cd7f32; border: 1px solid rgba(205, 127, 50, 0.3); }}
            #TierLabel[tier_class="silver"] {{ color: #c0c0c0; border: 1px solid rgba(192, 192, 192, 0.3); }}
            #TierLabel[tier_class="gold"] {{ color: #ffd700; border: 1px solid rgba(255, 215, 0, 0.3); }}
            #TierLabel[tier_class="diamond"] {{ color: #b9f2ff; border: 1px solid rgba(185, 242, 255, 0.3); }}
            #ItemDetailsV2 {{
                border-top: 1px solid rgba(255, 255, 255, 0.03);
                background: rgba(0, 0, 0, 0.12);
            }}
            /* ✅ 标签样式 - 紧凑扁平设计 */
            QLabel#TagBadge {{
                color: #8b9cff;
                background: rgba(122, 143, 255, 0.12);
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 8pt;
                font-weight: 500;
            }}
        """)
    
    def update_language(self):
        """更新语言"""
        # 重新初始化UI
        # 简化实现：只更新文本
        pass
