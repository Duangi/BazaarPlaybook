"""
历史战绩页面 - 重新设计版本
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QScrollArea, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from typing import Dict
import json
from pathlib import Path

from services.log_analyzer import LogAnalyzer
from utils.image_loader import ImageLoader, CardSize


class HistoryPageV2(QWidget):
    """历史战绩页面 - 重新设计"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化日志分析器
        from services.log_analyzer import get_log_directory
        log_dir = get_log_directory()
        
        # 传入 items_db 路径
        items_db_path = Path(__file__).parent.parent.parent / "assets" / "json" / "items_db.json"
        self.log_analyzer = LogAnalyzer(log_dir, str(items_db_path))
        
        # 加载物品数据库
        self.items_db = self._load_items_db()
        
        self._init_ui()
        self._show_click_to_load_message()
    
    def _load_items_db(self) -> dict:
        """加载物品数据库"""
        items_db_path = Path(__file__).parent.parent.parent / "assets" / "json" / "items_db.json"
        
        try:
            with open(items_db_path, 'r', encoding='utf-8') as f:
                items_list = json.load(f)
            
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
        
        # 清除缓存按钮
        clear_cache_btn = QPushButton("🗑️ 清除缓存")
        clear_cache_btn.setFixedWidth(120)
        clear_cache_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        clear_cache_btn.clicked.connect(self._clear_cache)
        clear_cache_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #fb8c00;
            }
        """)
        header_layout.addWidget(clear_cache_btn)
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setFixedWidth(100)
        refresh_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        refresh_btn.clicked.connect(self._load_matches)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
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
    
    def _clear_cache(self):
        """清除缓存"""
        try:
            cache_file = Path(__file__).parent.parent.parent / "user_data" / "game_sessions_cache.json"
            if cache_file.exists():
                cache_file.unlink()
                print("缓存已清除")
            
            # 重新加载
            self._load_matches()
        except Exception as e:
            print(f"清除缓存失败: {e}")
    
    def _show_click_to_load_message(self):
        """显示点击刷新按钮加载的提示信息"""
        while self.matches_layout.count():
            item = self.matches_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        hint_label = QLabel("点击右上角 🔄 刷新按钮\n加载游戏历史战绩")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #f59e0b;
                padding: 50px;
            }
        """)
        self.matches_layout.addWidget(hint_label)
    
    def _load_matches(self):
        """加载对局列表"""
        while self.matches_layout.count():
            item = self.matches_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        try:
            result = self.log_analyzer.analyze()
            sessions = result.get("sessions", [])
            
            if not sessions:
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
                for idx, session in enumerate(reversed(sessions), 1):
                    match_card = self._create_match_card(session, len(sessions) - idx + 1)
                    self.matches_layout.addWidget(match_card)
        except Exception as e:
            print(f"加载对局数据失败: {e}")
            import traceback
            traceback.print_exc()
        
        self.matches_layout.addStretch()
    
    def _create_match_card(self, session, game_number: int) -> QWidget:
        """创建对局卡片 - 现代化精美设计"""
        card_container = QWidget()
        container_layout = QVBoxLayout(card_container)
        container_layout.setContentsMargins(0, 0, 0, 10)
        container_layout.setSpacing(0)
        
        # 头部卡片
        header_card = QFrame()
        header_card.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # 胜利用渐变绿，失败用渐变红
        if session.victory:
            border_color = "#10b981"  # 翠绿
            gradient_start = "rgba(16, 185, 129, 0.15)"
            gradient_end = "rgba(5, 150, 105, 0.08)"
        else:
            border_color = "#ef4444"  # 鲜红
            gradient_start = "rgba(239, 68, 68, 0.15)"
            gradient_end = "rgba(220, 38, 38, 0.08)"
        
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(20, 15, 20, 15)
        header_layout.setSpacing(12)
        
        # 第一行
        top_row = QHBoxLayout()
        top_row.setSpacing(15)
        
        # 左侧信息
        left_info = QHBoxLayout()
        left_info.setSpacing(12)
        
        game_num_label = QLabel(f"游戏 #{game_number}")
        game_num_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #e5e7eb;
                background-color: rgba(255, 255, 255, 0.08);
                padding: 5px 14px;
                border-radius: 6px;
            }
        """)
        left_info.addWidget(game_num_label)
        
        # 结果 - 使用现代化圆形图标
        result_widget = QWidget()
        result_layout = QHBoxLayout(result_widget)
        result_layout.setContentsMargins(0, 0, 0, 0)
        result_layout.setSpacing(8)
        
        # 圆形状态指示器
        status_indicator = QLabel()
        status_indicator.setFixedSize(32, 32)
        status_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if session.victory:
            status_indicator.setStyleSheet("""
                QLabel {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #10b981, stop:1 #059669);
                    border-radius: 16px;
                    font-size: 18px;
                    font-weight: bold;
                    color: white;
                    border: 2px solid rgba(16, 185, 129, 0.3);
                }
            """)
            status_indicator.setText("✓")
        else:
            status_indicator.setStyleSheet("""
                QLabel {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #ef4444, stop:1 #dc2626);
                    border-radius: 16px;
                    font-size: 18px;
                    font-weight: bold;
                    color: white;
                    border: 2px solid rgba(239, 68, 68, 0.3);
                }
            """)
            status_indicator.setText("✗")
        result_layout.addWidget(status_indicator)
        
        status_text = QLabel("胜利" if session.victory else "失败")
        status_text.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: 600;
                color: {border_color};
            }}
        """)
        result_layout.addWidget(status_text)
        left_info.addWidget(result_widget)
        
        # 天数
        days_label = QLabel(f"第 {session.days} 天")
        days_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #fbbf24;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(251, 191, 36, 0.15),
                    stop:1 rgba(245, 158, 11, 0.1));
                padding: 5px 12px;
                border-radius: 6px;
                border: 1px solid rgba(251, 191, 36, 0.2);
            }
        """)
        left_info.addWidget(days_label)
        
        if session.hero:
            hero_label = QLabel(f"英雄: {session.hero}")
            hero_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #9ca3af;
                }
            """)
            left_info.addWidget(hero_label)
        
        top_row.addLayout(left_info)
        top_row.addStretch()
        
        # 右侧
        right_info = QHBoxLayout()
        right_info.setSpacing(15)
        
        if hasattr(session, 'start_datetime'):
            datetime_label = QLabel(session.start_datetime.strftime("%Y-%m-%d %H:%M:%S"))
            datetime_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #6b7280;
                }
            """)
            right_info.addWidget(datetime_label)
        elif session.start_time:
            time_label = QLabel(session.start_time)
            time_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #6b7280;
                }
            """)
            right_info.addWidget(time_label)
        
        expand_icon = QLabel("▼")
        expand_icon.setObjectName("expand_icon")
        expand_icon.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #9ca3af;
            }
        """)
        right_info.addWidget(expand_icon)
        
        top_row.addLayout(right_info)
        header_layout.addLayout(top_row)
        
        # 第二行：统计和图标
        bottom_row = QVBoxLayout()
        bottom_row.setSpacing(10)
        
        battles = session.pvp_battles
        total_battles = len(battles)
        wins = sum(1 for b in battles if b.get('victory', False))
        losses = total_battles - wins
        
        stats_label = QLabel(f"小局战绩: {wins} 胜 {losses} 负 (共 {total_battles} 场)")
        stats_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #d1d5db;
                font-weight: 500;
            }
        """)
        bottom_row.addWidget(stats_label)
        
        # 圆形图标 - 优化样式
        if battles:
            icons_container = QWidget()
            icons_layout = QVBoxLayout(icons_container)
            icons_layout.setContentsMargins(0, 0, 0, 0)
            icons_layout.setSpacing(6)
            
            for row_start in range(0, total_battles, 10):
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(8)
                
                for i in range(row_start, min(row_start + 10, total_battles)):
                    battle = battles[i]
                    is_win = battle.get('victory', False)
                    
                    icon_widget = QLabel()
                    icon_widget.setFixedSize(26, 26)
                    icon_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    if is_win:
                        icon_widget.setStyleSheet("""
                            QLabel {
                                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                    stop:0 #10b981, stop:1 #059669);
                                border-radius: 13px;
                                font-size: 15px;
                                font-weight: bold;
                                color: white;
                                border: 2px solid rgba(16, 185, 129, 0.4);
                            }
                        """)
                        icon_widget.setText("✓")
                    else:
                        icon_widget.setStyleSheet("""
                            QLabel {
                                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                    stop:0 #ef4444, stop:1 #dc2626);
                                border-radius: 13px;
                                font-size: 15px;
                                font-weight: bold;
                                color: white;
                                border: 2px solid rgba(239, 68, 68, 0.4);
                            }
                        """)
                        icon_widget.setText("✗")
                    
                    row_layout.addWidget(icon_widget)
                
                row_layout.addStretch()
                icons_layout.addWidget(row_widget)
            
            bottom_row.addWidget(icons_container)
        
        header_layout.addLayout(bottom_row)
        
        # 详情区域
        details_card = self._create_details_card(session)
        details_card.setVisible(False)
        details_card.setObjectName("details_card")
        
        container_layout.addWidget(header_card)
        container_layout.addWidget(details_card)
        
        # 卡片样式 - 使用渐变背景和美化边框
        header_card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {gradient_start},
                    stop:1 {gradient_end});
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-left: 4px solid {border_color};
                border-radius: 12px;
            }}
            QFrame:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 255, 255, 0.08),
                    stop:1 rgba(255, 255, 255, 0.03));
                border-color: rgba(255, 255, 255, 0.2);
                border-left-color: {border_color};
            }}
        """)
        
        def toggle_details(event):
            is_visible = details_card.isVisible()
            details_card.setVisible(not is_visible)
            expand_icon.setText("▲" if not is_visible else "▼")
        
        header_card.mousePressEvent = toggle_details
        
        return card_container
    
    def _create_details_card(self, session) -> QWidget:
        """创建详情卡片"""
        details_card = QFrame()
        details_layout = QVBoxLayout(details_card)
        details_layout.setContentsMargins(20, 15, 20, 15)
        details_layout.setSpacing(15)
        
        for idx, battle in enumerate(session.pvp_battles, 1):
            battle_detail = self._create_battle_detail(battle, idx)
            details_layout.addWidget(battle_detail)
            
            if idx < len(session.pvp_battles):
                separator = QFrame()
                separator.setFrameShape(QFrame.Shape.HLine)
                separator.setStyleSheet("background-color: rgba(255, 255, 255, 0.1);")
                details_layout.addWidget(separator)
        
        details_card.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 25, 20, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                margin-top: 5px;
            }
        """)
        
        return details_card
    
    def _create_battle_detail(self, battle: Dict, battle_num: int) -> QWidget:
        """创建单个小局详情 - 带物品图片"""
        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(10)
        
        # 标题行
        title_row = QHBoxLayout()
        
        num_label = QLabel(f"小局 #{battle_num}")
        num_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #ffcd19;
            }
        """)
        title_row.addWidget(num_label)
        
        is_win = battle.get('victory', False)
        result_icon = "✅ 胜利" if is_win else "❌ 失败"
        result_color = "#4CAF50" if is_win else "#f44336"
        
        result_label = QLabel(result_icon)
        result_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: bold;
                color: {result_color};
            }}
        """)
        title_row.addWidget(result_label)
        
        day_label = QLabel(f"| 第 {battle.get('day', '?')} 天")
        day_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #888888;
            }
        """)
        title_row.addWidget(day_label)
        
        if battle.get('start_time'):
            time_label = QLabel(f"| {battle.get('start_time')}")
            time_label.setStyleSheet("""
                QLabel {
                    font-size: 11px;
                    color: #666666;
                }
            """)
            title_row.addWidget(time_label)
        
        title_row.addStretch()
        detail_layout.addLayout(title_row)
        
        # 使用的物品 - 横向显示图片
        player_items = battle.get('player_items', [])
        if player_items:
            items_label = QLabel("使用物品:")
            items_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #aaaaaa;
                    margin-top: 5px;
                }
            """)
            detail_layout.addWidget(items_label)
            
            # 物品图片网格
            items_grid = QWidget()
            items_layout = QHBoxLayout(items_grid)
            items_layout.setContentsMargins(10, 5, 0, 0)
            items_layout.setSpacing(8)
            
            hand_items = [i for i in player_items if i.get('location') == 'Hand']
            
            for item in sorted(hand_items, key=lambda x: int(x.get('socket', 0)))[:10]:
                item_id = item.get('template_id', '')
                item_widget = self._create_item_icon(item_id)
                if item_widget:
                    items_layout.addWidget(item_widget)
            
            items_layout.addStretch()
            detail_layout.addWidget(items_grid)
        
        return detail_widget
    
    def _create_item_icon(self, item_id: str) -> QWidget:
        """创建物品图标（类似怪物详情中的掉落物）"""
        if not item_id or item_id == "unknown":
            return None
        
        # 获取物品数据
        item_data = self.items_db.get(item_id)
        if not item_data:
            return None
        
        # 获取物品大小
        size_str = item_data.get("size", "Medium / 中")
        size_en = size_str.split("/")[0].strip().lower()
        
        if "small" in size_en:
            card_size = CardSize.SMALL
        elif "large" in size_en:
            card_size = CardSize.LARGE
        else:
            card_size = CardSize.MEDIUM
        
        # 获取品级
        tier = item_data.get("starting_tier", "Bronze")
        if "/" in tier:
            tier = tier.split("/")[0].strip()
        tier_lower = tier.lower()
        
        # 边框颜色
        tier_colors = {
            "bronze": "#CD7F32",
            "silver": "#C0C0C0",
            "gold": "#FFD700",
            "diamond": "#B9F2FF",
            "legendary": "#FF4500"
        }
        border_color = tier_colors.get(tier_lower, "#CD7F32")
        
        # 计算尺寸
        base_height = 70
        if card_size == CardSize.SMALL:
            img_w = int(base_height * 0.5)
        elif card_size == CardSize.LARGE:
            img_w = int(base_height * 1.5)
        else:
            img_w = base_height
        
        img_h = base_height
        
        # 创建容器
        container = QLabel()
        container.setFixedSize(img_w + 4, img_h + 4)
        container.setStyleSheet(f"border: 2px solid {border_color}; border-radius: 4px; background: transparent;")
        
        # 加载图片
        pix = ImageLoader.load_card_image(item_id, card_size, height=img_h, with_border=False)
        if not pix.isNull():
            scaled = pix.scaled(img_w, img_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            container.setPixmap(scaled)
            container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        return container
    
    def refresh(self):
        """刷新页面"""
        self._load_matches()
