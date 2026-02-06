"""
怪物详情弹窗 (Monster Detail Dialog)
可拖拽、可调整大小的弹窗，显示怪物完整信息
"""
from typing import Dict
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QScrollArea, QGridLayout)
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QPixmap, QFont, QPainter, QCursor
from data_manager.monster_loader import Monster
from utils.i18n import get_i18n
from gui.utils.frameless_helper import FramelessHelper
from utils.image_loader import ImageLoader, CardSize
from gui.widgets.item_detail_card import ItemDetailCard
import os
import json


class MonsterDetailDialog(QWidget):
    """
    怪物详情悬浮窗
    - 鼠标悬浮在怪物卡片上显示
    - 可以鼠标移入交互
    - 鼠标移出自动隐藏
    """
    
    closed = Signal()  # 关闭信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_monster: Monster = None
        self.i18n = get_i18n()
        self.parent_widget = parent
        self.setMouseTracking(True)  # 启用鼠标追踪
        
        # 延迟关闭定时器
        self.close_timer = QTimer(self)
        self.close_timer.setSingleShot(True)
        self.close_timer.timeout.connect(self.close_dialog)
        
        self._init_window()
        self._init_ui()
    
    def _init_window(self):
        """初始化窗口属性"""
        # 使用 ToolTip 样式的窗口
        self.setWindowFlags(
            Qt.WindowType.ToolTip | 
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)  # 显示时不激活焦点
        self.setFixedSize(550, 650)  # 固定大小的悬浮窗
    
    def _init_ui(self):
        """初始化 UI"""
        # 根布局
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        
        # 主容器
        self.main_container = QFrame()
        self.main_container.setObjectName("MonsterDetailDialog")
        self.main_container.setStyleSheet("""
            #MonsterDetailDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(25, 25, 28, 0.98),
                    stop:1 rgba(15, 15, 18, 0.98));
                border: none;
                border-radius: 12px;
            }
        """)
        root_layout.addWidget(self.main_container)
        
        # 主容器布局
        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(15, 15, 15, 15)
        container_layout.setSpacing(12)
        
        # 滚动内容区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")  # 透明背景
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(15)
        
        scroll.setWidget(self.content_widget)
        container_layout.addWidget(scroll)
    
    def show_monster(self, monster: Monster, anchor_pos=None):
        """
        显示怪物详情
        Args:
            monster: 怪物对象
            anchor_pos: 锚点位置（QPoint 全局坐标），如果为 None 则显示在鼠标附近
        """
        self.current_monster = monster
        self._update_content()
        
        # 智能定位：确保不超出屏幕边界
        if anchor_pos:
            self._position_near(anchor_pos)
        else:
            from PySide6.QtGui import QCursor
            self._position_near(QCursor.pos())
        
        self.show()
        self.raise_()
    
    def set_monster_data(self, monster: Monster):
        """
        设置怪物数据（不显示窗口，用于抽屉面板）
        Args:
            monster: 怪物对象
        """
        self.current_monster = monster
        self._update_content()
    
    def _position_near(self, anchor_pos):
        """
        在锚点附近智能定位，避免超出屏幕边界
        Args:
            anchor_pos: QPoint 全局坐标
        """
        from PySide6.QtWidgets import QApplication
        
        screen = QApplication.primaryScreen().availableGeometry()
        dialog_width = self.width()
        dialog_height = self.height()
        
        # 默认显示在锚点右侧，稍微偏下
        x = anchor_pos.x() + 20
        y = anchor_pos.y() - 50
        
        # 检查右侧边界，如果超出则显示在左侧
        if x + dialog_width > screen.right():
            x = anchor_pos.x() - dialog_width - 20
        
        # 检查左侧边界
        if x < screen.left():
            x = screen.left() + 10
        
        # 检查底部边界
        if y + dialog_height > screen.bottom():
            y = screen.bottom() - dialog_height - 10
        
        # 检查顶部边界
        if y < screen.top():
            y = screen.top() + 10
        
        self.move(x, y)
    
    def enterEvent(self, event):
        """鼠标进入详情窗口 - 取消关闭"""
        self.close_timer.stop()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开详情窗口 - 延迟500ms关闭"""
        self.close_timer.start(500)
        super().leaveEvent(event)
    
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
        from utils.image_loader import ImageLoader
        pixmap = ImageLoader.load_monster_image(m.name_zh, size=70, with_border=True)
        avatar_label.setPixmap(pixmap)
        header_layout.addWidget(avatar_label)
        
        # 名字和血量（右侧）
        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)
        info_layout.addStretch()
        
        # 名字
        name = m.name_en if lang == "en_US" else m.name_zh
        if lang == "zh_TW":
            name = self.i18n.to_traditional(name)
        
        name_label = QLabel(name)
        name_label.setStyleSheet("color: #f59e0b; font-size: 16pt; font-weight: bold;")
        info_layout.addWidget(name_label)
        
        # 血量
        hp_label = QLabel(f"❤️ {m.health}")
        hp_label.setStyleSheet("color: #ff4444; font-size: 14pt; font-weight: bold;")
        info_layout.addWidget(hp_label)
        
        info_layout.addStretch()
        header_layout.addLayout(info_layout, 1)
        
        self.content_layout.addWidget(header_card)
        
        # 2. 技能列表（使用可展开卡片）
        if m.skills:
            self._add_section_title("技能" if lang == "zh_CN" else ("Skills" if lang == "en_US" else self.i18n.to_traditional("技能")))
            for skill in m.skills:
                skill_id = skill.get("id", "")
                current_tier = skill.get("current_tier", "bronze")
                
                # 使用新的可展开卡片组件
                skill_card = ItemDetailCard(skill_id, item_type="skill", current_tier=current_tier)
                self.content_layout.addWidget(skill_card)
        
        # 3. 掉落物品（横向排列图片）
        if m.items:
            self._add_section_title("掉落物品" if lang == "zh_CN" else ("Loot" if lang == "en_US" else self.i18n.to_traditional("掉落物品")))
            self._add_items_row(m.items)
        
        self.content_layout.addStretch()
    
    def _add_section_title(self, title: str):
        """添加章节标题"""
        label = QLabel(title)
        label.setStyleSheet("""
            color: #ffcc00;
            font-size: 15pt;
            font-weight: bold;
            padding: 10px 0px 5px 0px;
            border-bottom: 2px solid rgba(255, 204, 0, 0.3);
        """)
        self.content_layout.addWidget(label)
    
    def _load_item_from_db(self, item_id: str) -> Dict:
        """从 items_db.json 加载物品完整信息"""
        try:
            items_db_path = "assets/json/items_db.json"
            if os.path.exists(items_db_path):
                with open(items_db_path, 'r', encoding='utf-8') as f:
                    items_db = json.load(f)
                    for item in items_db:
                        if item.get("id") == item_id:
                            return item
        except Exception as e:
            print(f"Error loading item from DB: {e}")
        return {}
    
    def _add_items_row(self, items: list):
        """添加物品行（横向排列，只显示图片）"""
        items_container = QFrame()
        items_container.setStyleSheet("background: transparent;")
        
        items_layout = QHBoxLayout(items_container)
        items_layout.setContentsMargins(0, 0, 0, 0)
        items_layout.setSpacing(10)
        
        for item in items:
            item_id = item.get("id", "")
            
            # 从数据库获取物品信息
            item_data = self._load_item_from_db(item_id)
            if not item_data:
                continue
            
            # 获取物品大小
            size_str = item_data.get("size", "Medium / 中型")
            size_en = size_str.split("/")[0].strip().lower()
            
            if "small" in size_en:
                card_size = CardSize.SMALL
                size_suffix = "S"
            elif "large" in size_en:
                card_size = CardSize.LARGE
                size_suffix = "L"
            else:
                card_size = CardSize.MEDIUM
                size_suffix = "M"
            
            # 获取品级（从 tier 字段或 starting_tier）
            tier = item_data.get("tier", item_data.get("starting_tier", "Bronze"))
            tier = tier.split("/")[0].strip()  # 可能是 "Bronze / 青铜" 格式
            
            # 计算图片尺寸
            height = 80
            if card_size == CardSize.SMALL:
                width = int(height * 0.5)
            elif card_size == CardSize.LARGE:
                width = int(height * 1.5)
            else:
                width = height
            
            # 创建物品图标容器（使用 QLabel 叠加）
            item_container = QLabel()
            item_container.setFixedSize(width, height)
            item_container.setStyleSheet("border: none; background: transparent;")
            
            # 加载物品图片
            card_pixmap = ImageLoader.load_card_image(
                card_id=item_id,
                card_size=card_size,
                height=height,
                with_border=False
            )
            
            # 加载品级边框图片
            frame_path = f"assets/images/GUI/CardFrame_{tier}_{size_suffix}_TUI.webp"
            if os.path.exists(frame_path):
                # 合成图片：底层是卡牌，上层是边框
                from PySide6.QtGui import QPainter, QPixmap as QP
                
                result = QPixmap(width, height)
                result.fill(Qt.GlobalColor.transparent)
                
                painter = QPainter(result)
                # 绘制物品图片
                painter.drawPixmap(0, 0, width, height, card_pixmap)
                
                # 加载并绘制边框
                frame_pixmap = QPixmap(frame_path)
                if not frame_pixmap.isNull():
                    painter.drawPixmap(0, 0, width, height, frame_pixmap)
                
                painter.end()
                item_container.setPixmap(result)
            else:
                # 如果边框不存在，只显示物品图片
                item_container.setPixmap(card_pixmap)
            
            items_layout.addWidget(item_container)
        
        items_layout.addStretch()
        self.content_layout.addWidget(items_container)
    
    def close_dialog(self):
        """关闭弹窗"""
        self.closed.emit()
        self.hide()

    def update_language(self):
        """更新语言"""
        if self.current_monster:
            self._update_content()
