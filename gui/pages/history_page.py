"""
历史战绩页面
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QScrollArea)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
import json
from pathlib import Path

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
            QScrollBar:vertical {
                background: rgba(0, 0, 0, 0.2);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 205, 25, 0.3);
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 205, 25, 0.5);
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
        """加载对局列表 - 简化版，只显示结果和天数"""
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
                # 创建简化的对局卡片 - 倒序显示（最新的在上面）
                for session in reversed(sessions):
                    match_item = self._create_simple_match_card(session)
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
    
    def _create_simple_match_card(self, session) -> QWidget:
        """创建简化的对局卡片 - 只显示结果和天数"""
        card = QWidget()
        card.setFixedHeight(80)
        
        # 确定结果状态
        result_icon = "🏆" if session.victory else "💀"
        result_text = "胜利" if session.victory else "失败"
        result_color = "#4CAF50" if session.victory else "#f44336"
        
        # 主布局
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(20, 15, 20, 15)
        card_layout.setSpacing(20)
        
        # 左侧：结果图标和文字
        result_widget = QWidget()
        result_layout = QVBoxLayout(result_widget)
        result_layout.setContentsMargins(0, 0, 0, 0)
        result_layout.setSpacing(5)
        
        icon_label = QLabel(result_icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 32px;
            }}
        """)
        result_layout.addWidget(icon_label)
        
        status_label = QLabel(result_text)
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: bold;
                color: {result_color};
            }}
        """)
        result_layout.addWidget(status_label)
        
        card_layout.addWidget(result_widget)
        
        # 中间：分隔线
        separator = QLabel()
        separator.setFixedWidth(2)
        separator.setStyleSheet("background-color: rgba(255, 255, 255, 0.1);")
        card_layout.addWidget(separator)
        
        # 右侧：天数和时间信息
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(8)
        
        # 天数
        days_label = QLabel(f"存活天数: {session.days}")
        days_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #ffcd19;
            }
        """)
        info_layout.addWidget(days_label)
        
        # 时间（如果有）
        if session.start_time:
            time_label = QLabel(f"开始时间: {session.start_time}")
            time_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #888888;
                }
            """)
            info_layout.addWidget(time_label)
        
        # 英雄（如果有）
        if session.hero:
            hero_label = QLabel(f"英雄: {session.hero}")
            hero_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #888888;
                }
            """)
            info_layout.addWidget(hero_label)
        
        card_layout.addWidget(info_widget)
        card_layout.addStretch()
        
        # 卡片样式
        card.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(50, 45, 40, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-left: 4px solid {result_color};
                border-radius: 8px;
            }}
            QWidget:hover {{
                background-color: rgba(70, 60, 50, 0.7);
                border-color: rgba(255, 255, 255, 0.2);
            }}
        """)
        
        return card
    
    def refresh(self):
        """刷新页面"""
        self._load_matches()
