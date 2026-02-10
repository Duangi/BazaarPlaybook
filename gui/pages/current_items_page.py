"""
手头物品页面 - 显示当前游戏的所有物品
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea
)
from PySide6.QtCore import Qt
from pathlib import Path
import json
from gui.widgets.item_detail_card_v2 import ItemDetailCard
from gui.widgets.flow_layout import FlowLayout
from services.log_analyzer import LogAnalyzer


class CurrentItemsPage(QWidget):
    """手头物品页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 加载数据库
        self.items_db = self._load_items_db()
        
        # 日志分析器
        log_dir = Path(r"C:\Users\Admin\AppData\LocalLow\Tempo Storm\The Bazaar")
        self.analyzer = LogAnalyzer(str(log_dir))
        
        self._init_ui()
        
        # 初始加载
        self.refresh()
    
    def _load_items_db(self) -> list:
        """加载物品数据库"""
        items_db_path = Path(__file__).parent.parent.parent / "assets" / "json" / "items_db.json"
        try:
            with open(items_db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载物品数据库失败: {e}")
            return []
    
    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 标题栏
        header = QWidget()
        header.setFixedHeight(48)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 12, 20, 12)
        
        title_label = QLabel("手头物品")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #ffcd19;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(title_label)
        
        main_layout.addWidget(header)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 204, 0, 0.3);
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 204, 0, 0.5);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)
        
        # 内容容器
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(15)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(scroll_area)
    
    def refresh(self):
        """刷新物品列表"""
        # 清空现有内容
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 获取当前游戏状态
        result = self.analyzer.analyze()
        sessions = result.get('sessions', [])
        
        if not sessions:
            # 没有游戏会话
            empty_label = QLabel("暂无进行中的游戏")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("""
                QLabel {
                    font-size: 15px;
                    color: #888;
                    padding: 80px;
                }
            """)
            self.content_layout.addWidget(empty_label)
            return
        
        # 获取最后一个会话
        last_session = sessions[-1]
        
        # 如果会话已完成，显示提示
        if last_session.is_finished:
            finished_label = QLabel("上一局游戏已结束\n开始新游戏后将显示物品")
            finished_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            finished_label.setStyleSheet("""
                QLabel {
                    font-size: 15px;
                    color: #888;
                    padding: 80px;
                    line-height: 1.6;
                }
            """)
            self.content_layout.addWidget(finished_label)
            return
        
        # 获取当前物品
        current_items = last_session.get_current_items()
        hand_items = current_items.get('hand', [])
        storage_items = current_items.get('storage', [])
        
        if not hand_items and not storage_items:
            # 没有物品
            no_items_label = QLabel("当前没有物品")
            no_items_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_items_label.setStyleSheet("""
                QLabel {
                    font-size: 15px;
                    color: #888;
                    padding: 80px;
                }
            """)
            self.content_layout.addWidget(no_items_label)
            return
        
        # 显示手头物品
        if hand_items:
            hand_label = QLabel("手头物品")
            hand_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #ffcd19;
                    font-weight: bold;
                    padding-bottom: 8px;
                }
            """)
            self.content_layout.addWidget(hand_label)
            
            # 创建流式布局显示物品
            hand_flow_widget = QWidget()
            hand_flow_layout = FlowLayout(hand_flow_widget, margin=0, h_spacing=8, v_spacing=8)
            
            for item_data in hand_items:
                template_id = item_data.get('template_id')
                if template_id:
                    # 查找物品信息
                    item_info = next((item for item in self.items_db if item.get('id') == template_id), None)
                    if item_info:
                        card = ItemDetailCard(
                            item_id=template_id,
                            item_type="item",
                            item_data=item_info
                        )
                        hand_flow_layout.addWidget(card)
            
            self.content_layout.addWidget(hand_flow_widget)
        
        # 显示仓库物品
        if storage_items:
            storage_label = QLabel("仓库")
            storage_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #ffcd19;
                    font-weight: bold;
                    padding-top: 12px;
                    padding-bottom: 8px;
                }
            """)
            self.content_layout.addWidget(storage_label)
            
            # 创建流式布局显示物品
            storage_flow_widget = QWidget()
            storage_flow_layout = FlowLayout(storage_flow_widget, margin=0, h_spacing=8, v_spacing=8)
            
            for item_data in storage_items:
                template_id = item_data.get('template_id')
                if template_id:
                    # 查找物品信息
                    item_info = next((item for item in self.items_db if item.get('id') == template_id), None)
                    if item_info:
                        card = ItemDetailCard(
                            item_id=template_id,
                            item_type="item",
                            item_data=item_info
                        )
                        storage_flow_layout.addWidget(card)
            
            self.content_layout.addWidget(storage_flow_widget)
