"""
怪物详情弹窗 (Monster Detail Dialog)
可拖拽、可调整大小的弹窗，显示怪物完整信息
"""
from typing import Dict
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QScrollArea, QGridLayout)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap, QFont, QPainter
from data_manager.monster_loader import Monster
from utils.i18n import get_i18n
from gui.utils.frameless_helper import FramelessHelper
from utils.image_loader import ImageLoader, CardSize
from gui.widgets.item_detail_card import ItemDetailCard
import os
import json


class MonsterDetailDialog(QWidget):
    """
    怪物详情弹窗
    - 可拖拽
    - 可调整大小
    - 显示完整怪物信息
    """
    
    closed = Signal()  # 关闭信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_monster: Monster = None
        self.i18n = get_i18n()
        self._init_window()
        self._init_ui()
        
        # 安装事件过滤器到父窗口，监听全局点击
        if parent:
            parent.installEventFilter(self)
    
    def _init_window(self):
        """初始化窗口属性"""
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(500, 600)
        self.setMaximumSize(800, 1000)
        self.resize(650, 750)
        
        # 启用拖拽和调整大小
        self.frameless_helper = FramelessHelper(
            self,
            margin=5,
            snap_to_top=False,
            enable_drag=True,
            enable_resize=True,
            debug=False
        )
    
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
                border: 2px solid rgba(255, 204, 0, 0.4);
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
    
    def show_monster(self, monster: Monster):
        """显示怪物详情"""
        self.current_monster = monster
        self._update_content()
        self.show()
        self.raise_()
        self.activateWindow()
    
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
                background: rgba(40, 40, 45, 0.6);
                border: 1px solid rgba(245, 158, 11, 0.3);
                border-radius: 8px;
                padding: 15px;
            }
        """)
        header_layout = QHBoxLayout(header_card)
        header_layout.setSpacing(15)
        
        # 怪物头像（左侧，70x70）
        avatar_label = QLabel()
        avatar_label.setFixedSize(70, 70)
        from utils.image_loader import load_monster_avatar
        pixmap = load_monster_avatar(m.name_zh, size=70)
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
            
            # 从数据库获取物品信息（主要是 size）
            item_data = self._load_item_from_db(item_id)
            if not item_data:
                continue
            
            # 获取物品大小
            size_str = item_data.get("size", "Medium / 中型")
            # 解析 size（格式："Large / 大型"）
            size_en = size_str.split("/")[0].strip().lower()
            
            if "small" in size_en:
                card_size = CardSize.SMALL
            elif "large" in size_en:
                card_size = CardSize.LARGE
            else:
                card_size = CardSize.MEDIUM
            
            # 计算图片尺寸
            height = 80
            if card_size == CardSize.SMALL:
                width = int(height * 0.5)
            elif card_size == CardSize.LARGE:
                width = int(height * 1.5)
            else:
                width = height
            
            # 创建物品图标
            item_icon = QLabel()
            item_icon.setFixedSize(width, height)
            
            # 使用 ImageLoader 加载物品图片（带绿色边框）
            pixmap = ImageLoader.load_card_image(
                card_id=item_id,
                card_size=card_size,
                height=height,
                with_border=True
            )
            item_icon.setPixmap(pixmap)
            
            items_layout.addWidget(item_icon)
        
        items_layout.addStretch()
        self.content_layout.addWidget(items_container)
    
    def close_dialog(self):
        """关闭弹窗"""
        self.closed.emit()
        self.hide()
    
    def eventFilter(self, obj, event):
        """事件过滤器 - 检测点击外部关闭"""
        if event.type() == event.Type.MouseButtonPress:
            # 检查点击位置是否在对话框之外
            click_pos = event.globalPosition().toPoint()
            dialog_rect = self.geometry()
            
            if not dialog_rect.contains(click_pos):
                # 点击在对话框外部，关闭对话框
                self.close_dialog()
                return True
        
        return super().eventFilter(obj, event)
    
    def update_language(self):
        """更新语言"""
        if self.current_monster:
            self._update_content()
