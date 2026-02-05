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
    
    def __init__(self, item_id: str, item_type: str = "skill", 
                 current_tier: str = "bronze", parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self.item_type = item_type
        self.current_tier = current_tier.lower()
        self.i18n = get_i18n()
        self.is_expanded = False
        
        # 加载数据
        self.item_data = self._load_item_data()
        if not self.item_data:
            return
        
        self._init_ui()
    
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
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # 左侧：图标
        icon_size = 50
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
        center_layout.setSpacing(4)
        
        # 名称行
        name_layout = QHBoxLayout()
        name_layout.setSpacing(8)
        
        lang = self.i18n.get_language()
        name = self.item_data.get("name_cn" if lang != "en_US" else "name_en", "Unknown")
        if lang == "zh_TW":
            name = self.i18n.to_traditional(name)
        
        name_label = QLabel(name)
        name_label.setObjectName("NameCn")
        name_label.setStyleSheet("color: #fff; font-size: 17pt; font-weight: bold;")
        name_layout.addWidget(name_label)
        
        # 等级标签（根据 available_tiers 或 starting_tier）
        tier_display = self._get_tier_display_name()
        tier_label = QLabel(tier_display)
        tier_label.setObjectName("TierLabel")
        tier_label.setProperty("tier_class", self.current_tier)
        name_layout.addWidget(tier_label)
        name_layout.addStretch()
        
        center_layout.addLayout(name_layout)
        
        # 标签行（显示前3个processed_tags或tags）
        tags_layout = QHBoxLayout()
        tags_layout.setSpacing(4)
        tags = self.item_data.get("tags", "").split(" / ")[:3]
        for tag in tags:
            if tag.strip():
                tag_badge = QLabel(tag.strip())
                tag_badge.setObjectName("TagBadge")
                tag_badge.setStyleSheet("""
                    color: #98a8fe;
                    background: rgba(152, 168, 254, 0.15);
                    padding: 0 6px;
                    border-radius: 10px;
                    border: 1px solid rgba(152, 168, 254, 0.3);
                    font-size: 12pt;
                """)
                tags_layout.addWidget(tag_badge)
        tags_layout.addStretch()
        center_layout.addLayout(tags_layout)
        
        layout.addLayout(center_layout, 1)
        
        # 右侧：展开箭头
        self.expand_chevron = QLabel("▾")
        self.expand_chevron.setStyleSheet("color: rgba(255, 255, 255, 0.2); font-size: 16pt;")
        layout.addWidget(self.expand_chevron)
        
        return header
    
    def _create_details_widget(self) -> QWidget:
        """创建详情区域 - 参考 .item-details-v2"""
        details = QFrame()
        details.setObjectName("ItemDetailsV2")
        
        layout = QVBoxLayout(details)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # 等级切换按钮组
        self._add_tier_buttons(layout)
        
        # 技能描述区域
        self.description_container = QFrame()
        desc_layout = QVBoxLayout(self.description_container)
        desc_layout.setContentsMargins(0, 0, 0, 0)
        desc_layout.setSpacing(8)
        
        self._update_descriptions(desc_layout)
        
        layout.addWidget(self.description_container)
        
        return details
    
    def _add_tier_buttons(self, parent_layout: QVBoxLayout):
        """添加等级切换按钮"""
        available_tiers = self.item_data.get("available_tiers", "Bronze")
        tiers = [t.strip().lower() for t in available_tiers.replace("/", ",").split(",") if t.strip()]
        
        if len(tiers) <= 1:
            return  # 只有一个等级，不显示切换按钮
        
        tier_label = QLabel("等级:")
        tier_label.setStyleSheet("color: #f59e0b; font-size: 11pt; font-weight: bold;")
        parent_layout.addWidget(tier_label)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        self.tier_button_group = QButtonGroup(self)
        tier_names = {
            "bronze": "青铜",
            "silver": "白银",
            "gold": "黄金",
            "diamond": "钻石"
        }
        
        lang = self.i18n.get_language()
        if lang == "en_US":
            tier_names = {k: k.title() for k in tier_names}
        elif lang == "zh_TW":
            tier_names = {k: self.i18n.to_traditional(v) for k, v in tier_names.items()}
        
        for tier in ["bronze", "silver", "gold", "diamond"]:
            if tier in tiers:
                btn = QPushButton(tier_names.get(tier, tier.title()))
                btn.setCheckable(True)
                btn.setChecked(tier == self.current_tier)
                btn.setProperty("tier", tier)
                btn.setFixedHeight(30)
                btn.setStyleSheet(self._get_tier_button_style())
                btn.clicked.connect(lambda checked, t=tier: self._on_tier_changed(t))
                button_layout.addWidget(btn)
                self.tier_button_group.addButton(btn)
        
        button_layout.addStretch()
        parent_layout.addLayout(button_layout)
    
    def _update_descriptions(self, parent_layout: QVBoxLayout):
        """更新描述文本"""
        # 清空旧内容
        while parent_layout.count():
            item = parent_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        lang = self.i18n.get_language()
        descriptions = self.item_data.get("descriptions", [])
        
        for desc_obj in descriptions:
            desc_text = desc_obj.get("cn" if lang != "en_US" else "en", "")
            if lang == "zh_TW":
                desc_text = self.i18n.to_traditional(desc_text)
            
            if desc_text:
                desc_label = QLabel(f"• {desc_text}")
                desc_label.setWordWrap(True)
                desc_label.setStyleSheet("""
                    color: #e0e0e0;
                    font-size: 11pt;
                    background: rgba(30, 30, 35, 0.6);
                    border: 1px solid rgba(245, 158, 11, 0.2);
                    border-radius: 6px;
                    padding: 12px;
                """)
                parent_layout.addWidget(desc_label)
    
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
        """获取等级按钮样式"""
        return """
            QPushButton {
                background: rgba(60, 60, 65, 0.8);
                color: #ccc;
                border: 1px solid rgba(245, 158, 11, 0.2);
                border-radius: 6px;
                font-size: 10pt;
                padding: 5px 12px;
            }
            QPushButton:hover {
                background: rgba(70, 70, 75, 0.9);
                border: 1px solid rgba(245, 158, 11, 0.4);
            }
            QPushButton:checked {
                background: rgba(245, 158, 11, 0.3);
                border: 1px solid rgba(245, 158, 11, 0.6);
                color: #f59e0b;
                font-weight: bold;
            }
        """
    
    def _setup_style(self):
        """设置样式 - 完全参考 App.css"""
        self.setStyleSheet("""
            #ItemDetailCard {
                margin-bottom: 8px;
                background: rgba(30, 30, 30, 0.4);
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.05);
            }
            #ItemDetailCard:hover {
                background: rgba(50, 50, 50, 0.5);
                border-color: rgba(255, 255, 255, 0.15);
            }
            #ItemDetailCard[class="item-card-container expanded"] {
                background: rgba(25, 25, 25, 0.9);
                border-color: rgba(255, 205, 25, 0.3);
            }
            #ItemCardHeader {
                background: rgba(50, 45, 40, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
            }
            #ItemCardHeader:hover {
                background: rgba(70, 60, 40, 0.7);
            }
            #ImageBox {
                background: rgba(0, 0, 0, 0.4);
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            #TierLabel {
                font-size: 11pt;
                font-weight: 800;
                padding: 1px 4px;
                border-radius: 3px;
                background: rgba(255, 255, 255, 0.08);
                color: rgba(255, 255, 255, 0.5);
            }
            #TierLabel[tier_class="bronze"] { color: #cd7f32; border: 1px solid rgba(205, 127, 50, 0.3); }
            #TierLabel[tier_class="silver"] { color: #c0c0c0; border: 1px solid rgba(192, 192, 192, 0.3); }
            #TierLabel[tier_class="gold"] { color: #ffd700; border: 1px solid rgba(255, 215, 0, 0.3); }
            #TierLabel[tier_class="diamond"] { color: #b9f2ff; border: 1px solid rgba(185, 242, 255, 0.3); }
            #ItemDetailsV2 {
                border-top: 1px solid rgba(255, 255, 255, 0.05);
                background: rgba(0, 0, 0, 0.2);
            }
        """)
    
    def update_language(self):
        """更新语言"""
        # 重新初始化UI
        # 简化实现：只更新文本
        pass
