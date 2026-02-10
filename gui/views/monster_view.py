# gui/views/monster_view.py
"""怪物一览视图 - 使用重构后的组件"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
                              QFrame, QButtonGroup)
from PySide6.QtCore import Qt, Signal
from gui.components.day_pill import DayPill
from gui.components.monster_card import MonsterCard
from gui.components.styled_button import StyledButton

class MonsterView(QWidget):
    """怪物一览页面"""
    
    scan_requested = Signal()  # 请求扫描怪物
    monster_clicked = Signal(str)  # 点击怪物卡片
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_day = "Day 1"
        self.monsters_data = []  # 怪物数据列表
        
        self.setObjectName("MonsterView")
        self._setup_ui()
        self._setup_style()
        
    def _setup_ui(self):
        """设置UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 顶部控制栏
        control_bar = self._create_control_bar()
        main_layout.addWidget(control_bar)
        
        # 怪物列表滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("MonsterScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 怪物列表容器
        self.monster_list_widget = QWidget()
        self.monster_list_layout = QVBoxLayout(self.monster_list_widget)
        self.monster_list_layout.setContentsMargins(0, 0, 0, 0)
        self.monster_list_layout.setSpacing(8)
        self.monster_list_layout.addStretch()
        
        self.scroll_area.setWidget(self.monster_list_widget)
        main_layout.addWidget(self.scroll_area, 1)
        
    def _create_control_bar(self):
        """创建控制栏（天数选择 + 扫描按钮）"""
        bar = QFrame()
        bar.setObjectName("ControlBar")
        bar_layout = QVBoxLayout(bar)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setSpacing(8)
        
        # 天数选择器 - 横向滚动
        day_scroll = QScrollArea()
        day_scroll.setObjectName("DayScroll")
        day_scroll.setFixedHeight(50)
        day_scroll.setWidgetResizable(True)
        day_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        day_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        day_container = QWidget()
        day_layout = QHBoxLayout(day_container)
        day_layout.setContentsMargins(0, 0, 0, 0)
        day_layout.setSpacing(6)
        
        # 创建天数按钮组
        self.day_group = QButtonGroup(self)
        self.day_group.setExclusive(True)
        
        days = [f"Day {i}" for i in range(1, 10)] + ["Day 10+"]
        for day in days:
            day_pill = DayPill(day)
            self.day_group.addButton(day_pill)
            day_layout.addWidget(day_pill)
            day_pill.clicked.connect(lambda checked, d=day: self._on_day_changed(d))
            
        # 默认选中第一个
        self.day_group.buttons()[0].setChecked(True)
        
        day_scroll.setWidget(day_container)
        bar_layout.addWidget(day_scroll)
        
        # 扫描按钮
        scan_btn = StyledButton("🔍 扫描当前怪物", button_type="primary")
        scan_btn.setMinimumHeight(40)
        scan_btn.clicked.connect(self.scan_requested.emit)
        bar_layout.addWidget(scan_btn)
        
        return bar
        
    def _on_day_changed(self, day: str):
        """天数改变"""
        self.current_day = day
        self._update_monster_list()
        
    def set_monsters_data(self, monsters: list):
        """设置怪物数据"""
        self.monsters_data = monsters
        self._update_monster_list()
        
    def _update_monster_list(self):
        """更新怪物列表显示"""
        # 清空现有列表
        while self.monster_list_layout.count() > 1:  # 保留最后的stretch
            item = self.monster_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        # 过滤当前天数的怪物
        day_num = self._parse_day(self.current_day)
        filtered_monsters = [
            m for m in self.monsters_data 
            if day_num in m.get('available', [])
        ]
        
        # 添加怪物卡片
        for monster in filtered_monsters:
            card = MonsterCard(monster)
            card.clicked.connect(self.monster_clicked.emit)
            self.monster_list_layout.insertWidget(
                self.monster_list_layout.count() - 1,  # 插入到stretch前面
                card
            )
            
    def _parse_day(self, day_str: str) -> int:
        """解析天数字符串"""
        if day_str == "Day 10+":
            return 10
        return int(day_str.replace("Day ", ""))
        
    def highlight_monster(self, monster_id: str):
        """高亮显示指定怪物（刚识别出的）"""
        for i in range(self.monster_list_layout.count() - 1):
            widget = self.monster_list_layout.itemAt(i).widget()
            if isinstance(widget, MonsterCard):
                is_target = widget.monster_id == monster_id
                widget.set_identified(is_target)
                
    def _setup_style(self):
        """设置样式"""
        self.setStyleSheet("""
            #MonsterView {
                background: transparent;
            }
            
            #ControlBar {
                background: rgba(0, 0, 0, 0.2);
                border-radius: 8px;
                padding: 10px;
                border: 1px solid rgba(255, 255, 255, 0.05);
            }
            
            #DayScroll {
                background: rgba(0, 0, 0, 0.3);
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            #MonsterScrollArea {
                background: transparent;
                border: none;
            }
            
            QScrollArea QScrollBar:vertical {
                background: rgba(0, 0, 0, 0.3);
                width: 10px;
                border-radius: 5px;
                border: 1px solid rgba(255, 204, 0, 0.1);
            }
            
            QScrollArea QScrollBar::handle:vertical {
                background: linear-gradient(180deg, 
                    rgba(255, 204, 0, 0.7), 
                    rgba(255, 180, 0, 0.6));
                border-radius: 5px;
                border: 1px solid rgba(255, 204, 0, 0.3);
                min-height: 20px;
            }
            
            QScrollArea QScrollBar::handle:vertical:hover {
                background: linear-gradient(180deg, 
                    rgba(255, 215, 0, 0.9), 
                    rgba(255, 190, 0, 0.8));
            }
            
            QScrollArea QScrollBar::add-line:vertical,
            QScrollArea QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
