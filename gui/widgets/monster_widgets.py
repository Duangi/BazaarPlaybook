"""
野怪组件 (Monster Widgets)
包含怪物简介卡片
"""
from typing import Dict
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QScrollArea, QGridLayout)
from PySide6.QtCore import Qt, Signal, QSize, QTimer
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
    hovered = Signal(Monster)  # 悬浮时发送怪物对象
    hover_leave = Signal()     # 离开时发送信号
    
    def __init__(self, monster: Monster, parent=None):
        super().__init__(parent)
        self.monster = monster
        self.i18n = get_i18n()
        
        # 悬浮定时器（200ms 后触发）
        self.hover_timer = QTimer(self)
        self.hover_timer.setSingleShot(True)
        self.hover_timer.setInterval(200)
        self.hover_timer.timeout.connect(self._on_hover_timeout)
        
        self.setMouseTracking(True)
        
        self._init_ui()
        self._setup_style()
    
    def _init_ui(self):
        """初始化 UI - 战术目镜风格"""
        self.setObjectName("MonsterCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(90)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 15, 0)
        layout.setSpacing(15)
        
        # 🔶 左侧金色指示线
        self.indicator_line = QFrame()
        self.indicator_line.setObjectName("IndicatorLine")
        self.indicator_line.setFixedWidth(2)
        layout.addWidget(self.indicator_line)
        
        # 1. 怪物头像（硬币质感，1px 亮金边）
        avatar_container = QWidget()
        avatar_container.setFixedSize(65, 65)
        avatar_container.setStyleSheet("""
            QWidget {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
                    fx:0.3, fy:0.3,
                    stop:0 rgba(255, 215, 0, 0.2),
                    stop:0.8 rgba(212, 175, 55, 0.1),
                    stop:1 rgba(139, 115, 85, 0.3));
                border: 1px solid #D4AF37;
                border-radius: 33px;
            }
        """)
        
        avatar_layout = QVBoxLayout(avatar_container)
        avatar_layout.setContentsMargins(3, 3, 3, 3)
        
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(59, 59)
        self.avatar_label.setScaledContents(False)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 加载怪物图片
        pixmap = load_monster_avatar(self.monster.name_zh, size=59)
        self.avatar_label.setPixmap(pixmap)
        
        avatar_layout.addWidget(self.avatar_label)
        layout.addWidget(avatar_container)
        
        # 2. 信息区域（中间）
        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加顶部弹性空间，实现垂直居中
        info_layout.addStretch()
        
        # 怪物名字（大号加粗）
        self.name_label = QLabel()
        self.name_label.setObjectName("MonsterName")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.name_label.setFont(font)
        info_layout.addWidget(self.name_label)
        
        # 血量文字
        self.hp_label = QLabel()
        self.hp_label.setObjectName("MonsterHP")
        self.hp_label.setStyleSheet("color: #ff6b6b; font-size: 10pt; font-weight: 600;")
        info_layout.addWidget(self.hp_label)
        
        # 血量进度条（3px 暗红发光）
        self.hp_bar = QFrame()
        self.hp_bar.setFixedHeight(3)
        self.hp_bar.setObjectName("HPBar")
        self.hp_bar.setStyleSheet("""
            #HPBar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff0000,
                    stop:0.6 #ff4444,
                    stop:1 #ff6666);
                border-radius: 2px;
                border: none;
            }
        """)
        info_layout.addWidget(self.hp_bar)
        
        # 添加底部弹性空间，实现垂直居中
        info_layout.addStretch()
        
        layout.addLayout(info_layout, 1)
        
        # 3. 右侧详情箭头
        arrow_label = QLabel("❯")
        arrow_label.setObjectName("DetailArrow")
        arrow_label.setStyleSheet("""
            #DetailArrow {
                color: rgba(212, 175, 55, 0.5);
                font-size: 18pt;
                font-weight: bold;
            }
        """)
        layout.addWidget(arrow_label)
        
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
        """设置战术目镜风格样式"""
        self.setStyleSheet("""
            #MonsterCard {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(25, 22, 20, 0.95),
                    stop:1 rgba(18, 16, 14, 0.95));
                border: 1px solid rgba(255, 204, 0, 0.08);
                border-radius: 4px;
            }
            #MonsterCard:hover {
                /* 暗金磨砂质感 */
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(50, 45, 35, 0.92),
                    stop:0.5 rgba(60, 52, 38, 0.95),
                    stop:1 rgba(50, 45, 35, 0.92));
                border: 1px solid rgba(212, 175, 55, 0.35);
                box-shadow: 0 2px 8px rgba(212, 175, 55, 0.15);
            }
            #MonsterName {
                color: #FFFFFF;
            }
            /* 左侧金色指示线 */
            #IndicatorLine {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(212, 175, 55, 0.3),
                    stop:0.5 rgba(255, 215, 0, 0.5),
                    stop:1 rgba(212, 175, 55, 0.3));
            }
            #MonsterCard:hover #IndicatorLine {
                /* Hover 时扩张到 5px 并脉冲发光 */
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 215, 0, 0.7),
                    stop:0.5 rgba(255, 235, 100, 0.9),
                    stop:1 rgba(255, 215, 0, 0.7));
                min-width: 5px;
                max-width: 5px;
            }
            #MonsterCard:hover #DetailArrow {
                color: rgba(255, 215, 0, 0.9);
            }
        """)
    
    def enterEvent(self, event):
        """鼠标进入 - 启动悬浮定时器"""
        self.hover_timer.start()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开 - 取消定时器并发送离开信号"""
        self.hover_timer.stop()
        self.hover_leave.emit()
        super().leaveEvent(event)
    
    def _on_hover_timeout(self):
        """悬浮定时器超时 - 发送悬浮信号"""
        self.hovered.emit(self.monster)
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.monster)
        super().mousePressEvent(event)
