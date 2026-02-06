"""
怪物详情内容组件 (Monster Detail Content Widget)
用于在抽屉面板中显示怪物详情
"""
from typing import Dict
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QScrollArea, QGridLayout)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QFont, QPainter
from data_manager.monster_loader import Monster
from utils.i18n import get_i18n
from utils.image_loader import ImageLoader, CardSize
from gui.widgets.item_detail_card import ItemDetailCard
import os
import json


class MonsterDetailContent(QWidget):
    """
    怪物详情内容组件（纯内容，无窗口属性）
    用于在抽屉面板中显示
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_monster: Monster = None
        self.i18n = get_i18n()
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 滚动内容区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(15)
        self.content_layout.setContentsMargins(15, 15, 15, 15)
        
        scroll.setWidget(self.content_widget)
        main_layout.addWidget(scroll)
    
    def set_monster(self, monster: Monster):
        """
        设置要显示的怪物
        Args:
            monster: 怪物对象
        """
        self.current_monster = monster
        self._update_content()
    
    def _update_content(self):
        """更新详情内容"""
        # 清空旧内容
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.current_monster:
            return
        
        m = self.current_monster
        lang = self.i18n.get_language()
        
        # 1. 怪物头像 + 基础信息
        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
                padding: 0px;
            }
        """)
        header_layout = QHBoxLayout(header_card)
        header_layout.setSpacing(15)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # 怪物头像（左侧，70x70）
        avatar_label = QLabel()
        avatar_label.setFixedSize(70, 70)
        avatar_label.setStyleSheet("border: none; background: transparent;")
        pixmap = ImageLoader.load_monster_image(m.name_zh, size=70, with_border=True)
        avatar_label.setPixmap(pixmap)
        header_layout.addWidget(avatar_label)
        
        # 名字和血量（右侧）
        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)
        info_layout.addStretch()
        
        # 名字
        name_text = m.name_zh if lang == "zh_CN" else (m.name_tw if lang == "zh_TW" else m.name_en)
        name_label = QLabel(name_text)
        name_label.setStyleSheet("font-size: 16pt; font-weight: bold; color: #f59e0b;")
        info_layout.addWidget(name_label)
        
        # 血量
        hp_label = QLabel(f"❤️ {m.health}")
        hp_label.setStyleSheet("font-size: 12pt; color: #ff5555;")
        info_layout.addWidget(hp_label)
        
        info_layout.addStretch()
        header_layout.addLayout(info_layout)
        
        self.content_layout.addWidget(header_card)
        
        # 2. 技能列表
        if m.skills:
            skills_label = QLabel("🎯 技能")
            skills_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #ffffff; margin-top: 10px;")
            self.content_layout.addWidget(skills_label)
            
            for skill in m.skills:
                skill_card = ItemDetailCard(skill, item_type="skill")
                self.content_layout.addWidget(skill_card)
        
        # 3. 掉落物品
        if m.items:
            loot_label = QLabel("💰 掉落")
            loot_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #ffffff; margin-top: 10px;")
            self.content_layout.addWidget(loot_label)
            
            for item in m.items:
                item_card = ItemDetailCard(item, item_type="item")
                self.content_layout.addWidget(item_card)
        
        # 底部弹性空间
        self.content_layout.addStretch()
    
    def update_language(self):
        """更新语言"""
        if self.current_monster:
            self._update_content()
