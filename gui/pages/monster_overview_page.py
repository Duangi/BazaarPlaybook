"""
野怪一览页面 (Monster Overview Page)
包含 Day1-Day10+ 按钮切换和怪物列表
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QScrollArea, QButtonGroup)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from gui.widgets.monster_widgets import MonsterCard
from gui.widgets.monster_detail_float_window import MonsterDetailFloatWindow
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
        
        # 详情悬浮窗（独立窗口）
        self.detail_window = None
        
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
        """创建 Day 按钮行（两排显示）"""
        from PySide6.QtWidgets import QGridLayout
        
        container = QFrame()
        container.setFixedHeight(90)  # 增加高度以容纳两排
        layout = QGridLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        # 创建按钮组（互斥选中）
        self.day_button_group = QButtonGroup(self)
        self.day_button_group.setExclusive(True)
        
        # 获取所有可用的天数
        all_days = self.monster_db.get_all_days()
        
        # 创建按钮（Day 1, Day 2, ..., Day 10+）分两排
        # 第一排：Day 1-5
        # 第二排：Day 6-10+
        for idx, day in enumerate(all_days):
            btn = QPushButton(f"Day {day}" if day <= 10 else "Day 10+")
            btn.setCheckable(True)
            btn.setChecked(day == 1)  # 默认选中 Day 1
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(38)
            btn.setProperty("day", day)  # 存储天数
            
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(40, 40, 45, 0.8);
                    color: #cccccc;
                    font-size: 11pt;
                    font-weight: 600;
                    border: 1px solid rgba(255, 204, 0, 0.2);
                    border-radius: 6px;
                    padding: 0px 8px;
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
                    border: 2px solid rgba(255, 204, 0, 0.8);
                    font-weight: 700;
                }
            """)
            
            btn.clicked.connect(lambda checked, d=day: self.load_day(d))
            self.day_button_group.addButton(btn, day)
            
            # 计算行列位置：前5个在第一排，后面的在第二排
            row = 0 if idx < 5 else 1
            col = idx if idx < 5 else idx - 5
            layout.addWidget(btn, row, col)
        
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
                # 连接悬浮和离开事件
                card.hovered.connect(self._on_monster_hovered)
                card.hover_leave.connect(self._on_monster_hover_leave)
                self.monster_list_layout.addWidget(card)
                self.monster_cards.append(card)
        
        # 底部弹性空间
        self.monster_list_layout.addStretch()
    
    def show_floating_detail_by_id(self, monster_id: str):
        """通过ID显示浮动详情"""
        if not monster_id:
            return
            
        monster = self.monster_db.get_monster_by_id(monster_id)
        if monster:
            if self.detail_window is None:
                self.detail_window = MonsterDetailFloatWindow()
            self.detail_window.show_floating(monster)

    def show_floating_item_detail_by_id(self, item_id):
        """显示卡牌/物品详情"""
        if not item_id:
            return

        if self.detail_window is None:
            self.detail_window = MonsterDetailFloatWindow()
            
        parent_window = self.window()
        # Ensure we use show_item_beside which we just added
        if hasattr(self.detail_window, 'show_item_beside'):
            self.detail_window.show_item_beside(parent_window, item_id)
        else:
            print("Error: MonsterDetailFloatWindow missing show_item_beside")
    
    def hide_detail(self):
        if self.detail_window:
            self.detail_window.request_hide()

    def reset_detail_window_position(self):
        """重置悬浮窗位置"""
        if self.detail_window is None:
            self.detail_window = MonsterDetailFloatWindow()
        self.detail_window.reset_position()
        if self.detail_window.isVisible():
            self.detail_window.raise_()

    def _on_monster_hovered(self, monster: Monster):
        """怪物卡片被悬浮 - 在侧边显示详情"""
        # 第一次悬浮时创建详情窗口
        if self.detail_window is None:
            self.detail_window = MonsterDetailFloatWindow()
        
        # 获取主窗口（SidebarWindow）
        parent_window = self.window()
        
        # 在主窗口旁边显示详情（自动判断左右）
        self.detail_window.show_beside(parent_window, monster)
    
    def _on_monster_hover_leave(self):
        """鼠标离开怪物卡片 - 请求隐藏详情窗口"""
        if self.detail_window and self.detail_window.isVisible():
            self.detail_window.request_hide()
    
    def _on_scan_all_clicked(self):
        """一键识别所有野怪"""
        print("[Monster Overview] 一键识别功能待实现")
        # TODO: 调用识别服务
    
    def update_language(self):
        """更新语言"""
        # 重新加载当前天数（刷新卡片文本）
        self.load_day(self.current_day)
        # 更新详情窗口（如果存在）
        if self.detail_window:
            self.detail_window.update_language()
