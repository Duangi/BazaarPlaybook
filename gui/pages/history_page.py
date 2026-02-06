"""
历史战绩页面
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QScrollArea)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
import json
from pathlib import Path

from gui.widgets.match_history_widgets import MatchListItem
from services.log_analyzer import LogAnalyzer


class HistoryPage(QWidget):
    """历史战绩页面 - 从游戏日志中读取真实数据"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化日志分析器 - 使用默认日志目录
        from services.log_analyzer import get_log_directory
        log_dir = get_log_directory()
        self.log_analyzer = LogAnalyzer(log_dir)
        
        # 加载物品数据库
        self.items_db = self._load_items_db()
        
        self._init_ui()
        self._load_matches()
    
    def _load_items_db(self) -> dict:
        """加载物品数据库"""
        items_db_path = Path(__file__).parent.parent.parent / "assets" / "json" / "items_db.json"
        
        try:
            with open(items_db_path, 'r', encoding='utf-8') as f:
                items_list = json.load(f)
            
            # 转换为字典（以id为键）
            items_dict = {}
            for item in items_list:
                item_id = item.get('id')
                if item_id:
                    items_dict[item_id] = item
            
            return items_dict
        except Exception as e:
            print(f"加载物品数据库失败: {e}")
            return {}
    
    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 标题栏
        header = self._create_header()
        main_layout.addWidget(header)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # 对局列表容器
        self.matches_container = QWidget()
        self.matches_layout = QVBoxLayout(self.matches_container)
        self.matches_layout.setContentsMargins(0, 0, 0, 0)
        self.matches_layout.setSpacing(10)
        
        scroll_area.setWidget(self.matches_container)
        main_layout.addWidget(scroll_area)
        
        # 页面样式
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
    
    def _create_header(self) -> QWidget:
        """创建标题栏"""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("历史战绩")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #ffffff;
            }
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.setFixedWidth(80)
        refresh_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        refresh_btn.clicked.connect(self._load_matches)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px 15px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        header_layout.addWidget(refresh_btn)
        
        return header
    
    def _load_matches(self):
        """加载对局列表 - 从日志分析器获取真实数据"""
        # 清空现有列表
        while self.matches_layout.count():
            item = self.matches_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        try:
            # 分析日志获取游戏会话
            result = self.log_analyzer.analyze()
            sessions = result.get("sessions", [])
            
            if not sessions:
                # 显示空状态
                empty_label = QLabel("暂无历史战绩\n\n请先进行游戏，日志将自动记录")
                empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_label.setStyleSheet("""
                    QLabel {
                        font-size: 16px;
                        color: #888888;
                        padding: 50px;
                    }
                """)
                self.matches_layout.addWidget(empty_label)
            else:
                # 创建对局卡片 - 倒序显示（最新的在上面）
                for session in reversed(sessions):
                    # 转换session数据为match_data格式
                    match_data = self._convert_session_to_match(session)
                    match_item = MatchListItem(match_data, self.items_db)
                    self.matches_layout.addWidget(match_item)
        except Exception as e:
            print(f"加载对局数据失败: {e}")
            import traceback
            traceback.print_exc()
            
            error_label = QLabel(f"加载失败: {str(e)}")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #ff6666;
                    padding: 30px;
                }
            """)
            self.matches_layout.addWidget(error_label)
        
        # 添加弹簧
        self.matches_layout.addStretch()
    
    def _convert_session_to_match(self, session) -> dict:
        """将GameSession转换为match_data格式"""
        return {
            "match_id": f"session_{id(session)}",  # 使用session对象的id作为唯一标识
            "hero": session.hero if session.hero else "Unknown",  # 使用session中的英雄名称
            "start_time": session.start_time or "",
            "end_time": session.end_time or "",
            "days": session.days,
            "victory": session.victory,
            "is_finished": session.is_finished,
            "created_at": session.start_time or "",
            "pvp_battles": session.pvp_battles  # 直接使用session中的pvp_battles列表
        }
    
    def refresh(self):
        """刷新页面"""
        self._load_matches()
