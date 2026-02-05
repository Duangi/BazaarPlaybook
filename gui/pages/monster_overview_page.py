"""
野怪一览页面 (Monster Overview Page)
包含 Day1-Day10+ 按钮切换和怪物列表
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QScrollArea, QButtonGroup)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from gui.widgets.monster_widgets import MonsterCard
from gui.widgets.monster_detail_dialog import MonsterDetailDialog
from data_manager.monster_loader import get_monster_db, Monster
from utils.i18n import get_i18n


class MonsterOverviewPage(QWidget):
    """
    野怪一览页面
    只显示怪物简介列表，点击后弹出详情窗口
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.monster_db = get_monster_db()
        self.i18n = get_i18n()
        self.current_day = 1
        self.monster_cards = []  # 当前显示的卡片列表
        self.detail_dialog = None  # 详情弹窗
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        # 主布局：单列
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 1. 顶部工具栏
        toolbar = self._create_toolbar()
        main_layout.addWidget(toolbar)
        
        # 2. Day 按钮行
        day_buttons = self._create_day_buttons()
        main_layout.addWidget(day_buttons)
        
        # 3. 怪物列表（滚动区域）
        self.monster_list_scroll = QScrollArea()
        self.monster_list_scroll.setWidgetResizable(True)
        self.monster_list_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.monster_list_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.monster_list_widget = QWidget()
        self.monster_list_widget.setStyleSheet("background: transparent;")  # 修复白色背景
        self.monster_list_layout = QVBoxLayout(self.monster_list_widget)
        self.monster_list_layout.setSpacing(8)
        self.monster_list_layout.setContentsMargins(0, 0, 0, 0)
        
        self.monster_list_scroll.setWidget(self.monster_list_widget)
        main_layout.addWidget(self.monster_list_scroll)
        
        # 默认加载 Day 1
        self.load_day(1)
    
    def _create_toolbar(self) -> QWidget:
        """创建顶部工具栏（一键识别按钮）"""
        toolbar = QFrame()
        toolbar.setFixedHeight(50)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # 一键识别按钮
        scan_all_btn = QPushButton("🔍 一键识别所有野怪")
        scan_all_btn.setObjectName("ScanAllButton")
        scan_all_btn.setCursor(Qt.PointingHandCursor)
        scan_all_btn.setFixedHeight(40)
        scan_all_btn.setStyleSheet("""
            #ScanAllButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 204, 0, 0.8),
                    stop:1 rgba(255, 180, 0, 0.8));
                color: #000000;
                font-size: 13pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
            }
            #ScanAllButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 220, 50, 0.9),
                    stop:1 rgba(255, 200, 50, 0.9));
            }
            #ScanAllButton:pressed {
                background: rgba(200, 150, 0, 0.9);
            }
        """)
        scan_all_btn.clicked.connect(self._on_scan_all_clicked)
        toolbar_layout.addWidget(scan_all_btn)
        
        return toolbar
    
    def _create_day_buttons(self) -> QWidget:
        """创建 Day 按钮行"""
        container = QFrame()
        container.setFixedHeight(45)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # 创建按钮组（互斥选中）
        self.day_button_group = QButtonGroup(self)
        self.day_button_group.setExclusive(True)
        
        # 获取所有可用的天数
        all_days = self.monster_db.get_all_days()
        
        # 创建按钮（Day 1, Day 2, ..., Day 10+）
        for day in all_days:
            btn = QPushButton(f"Day {day}" if day <= 10 else "Day 10+")
            btn.setCheckable(True)
            btn.setChecked(day == 1)  # 默认选中 Day 1
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(35)
            btn.setProperty("day", day)  # 存储天数
            
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(40, 40, 45, 0.8);
                    color: #cccccc;
                    font-size: 10pt;
                    font-weight: 600;
                    border: 1px solid rgba(255, 204, 0, 0.2);
                    border-radius: 6px;
                    padding: 0px 12px;
                }
                QPushButton:hover {
                    background: rgba(50, 50, 55, 0.9);
                    border: 1px solid rgba(255, 204, 0, 0.4);
                }
                QPushButton:checked {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(255, 204, 0, 0.3),
                        stop:1 rgba(255, 180, 0, 0.3));
                    color: #ffcc00;
                    border: 1px solid rgba(255, 204, 0, 0.6);
                }
            """)
            
            btn.clicked.connect(lambda checked, d=day: self.load_day(d))
            self.day_button_group.addButton(btn, day)
            layout.addWidget(btn)
        
        layout.addStretch()
        return container
    
    def load_day(self, day: int):
        """加载指定天的怪物列表"""
        self.current_day = day
        
        # 清空旧列表
        while self.monster_list_layout.count():
            item = self.monster_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.monster_cards.clear()
        
        # 加载新怪物
        monsters = self.monster_db.get_monsters_by_day(day)
        
        if not monsters:
            # 显示"暂无怪物"提示
            empty_label = QLabel("该天数暂无怪物数据")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #888888; font-size: 12pt; padding: 40px;")
            self.monster_list_layout.addWidget(empty_label)
        else:
            for monster in monsters:
                card = MonsterCard(monster)
                card.clicked.connect(self._on_monster_clicked)
                self.monster_list_layout.addWidget(card)
                self.monster_cards.append(card)
        
        # 底部弹性空间
        self.monster_list_layout.addStretch()
    
    def _on_monster_clicked(self, monster: Monster):
        """怪物卡片被点击 - 显示详情弹窗"""
        if self.detail_dialog is None:
            self.detail_dialog = MonsterDetailDialog(self)
        
        self.detail_dialog.show_monster(monster)
    
    def _on_scan_all_clicked(self):
        """一键识别所有野怪"""
        print("[Monster Overview] 一键识别功能待实现")
        # TODO: 调用识别服务
    
    def update_language(self):
        """更新语言"""
        # 重新加载当前天数（刷新卡片文本）
        self.load_day(self.current_day)
        # 更新详情弹窗（如果存在且可见）
        if self.detail_dialog and self.detail_dialog.isVisible():
            self.detail_dialog.update_language()
