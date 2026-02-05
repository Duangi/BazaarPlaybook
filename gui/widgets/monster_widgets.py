"""
野怪组件 (Monster Widgets)
包含怪物简介卡片
"""
from typing import Dict
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QScrollArea, QGridLayout)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap, QFont
from data_manager.monster_loader import Monster
from utils.i18n import get_i18n
from utils.image_loader import load_monster_avatar


class MonsterCard(QFrame):
    """
    怪物简介卡片
    显示：怪物图片、名字、血量
    """
    clicked = Signal(Monster)  # 点击时发送怪物对象
    
    def __init__(self, monster: Monster, parent=None):
        super().__init__(parent)
        self.monster = monster
        self.i18n = get_i18n()
        self._init_ui()
        self._setup_style()
    
    def _init_ui(self):
        """初始化 UI"""
        self.setObjectName("MonsterCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(100)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)
        
        # 1. 怪物图片（左侧圆形头像 - 使用 ImageLoader）
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(70, 70)
        self.avatar_label.setScaledContents(False)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 加载怪物图片
        pixmap = load_monster_avatar(self.monster.name_zh, size=70)
        self.avatar_label.setPixmap(pixmap)
        
        layout.addWidget(self.avatar_label)
        
        # 2. 信息区域（中间）
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加顶部弹性空间，实现垂直居中
        info_layout.addStretch()
        
        # 怪物名字
        self.name_label = QLabel()
        self.name_label.setObjectName("MonsterName")
        font = QFont()
        font.setPointSize(13)
        font.setBold(True)
        self.name_label.setFont(font)
        info_layout.addWidget(self.name_label)
        
        # 血量显示
        self.hp_label = QLabel()
        self.hp_label.setObjectName("MonsterHP")
        self.hp_label.setStyleSheet("color: #ff4444; font-size: 11pt;")
        info_layout.addWidget(self.hp_label)
        
        # 添加底部弹性空间，实现垂直居中
        info_layout.addStretch()
        
        layout.addLayout(info_layout, 1)
        
        # 更新文本
        self.update_text()
    
    def update_text(self):
        """更新本地化文本"""
        lang = self.i18n.get_language()
        
        if lang == "en_US":
            name = self.monster.name_en
        else:
            name = self.monster.name_zh
            if lang == "zh_TW":
                name = self.i18n.to_traditional(name)
        
        self.name_label.setText(name)
        
        # 血量（带爱心图标）
        hp_text = self.i18n.translate("血量", "HP") if lang != "zh_CN" else "血量"
        self.hp_label.setText(f"❤️ {self.monster.health}")
    
    def _setup_style(self):
        """设置样式"""
        self.setStyleSheet("""
            #MonsterCard {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(30, 30, 32, 0.95),
                    stop:1 rgba(20, 20, 22, 0.95));
                border: 1px solid rgba(255, 204, 0, 0.15);
                border-radius: 8px;
            }
            #MonsterCard:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(40, 40, 42, 0.98),
                    stop:1 rgba(30, 30, 32, 0.98));
                border: 1px solid rgba(255, 204, 0, 0.4);
            }
            #MonsterName {
                color: #f0f0f0;
            }
        """)
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.monster)
        super().mousePressEvent(event)
