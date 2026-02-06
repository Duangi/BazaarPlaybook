"""
历史战绩页面组件
"""
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QScrollArea)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QCursor
from typing import Dict


class DayBattleCard(QWidget):
    """单天战斗卡片"""
    
    screenshot_clicked = Signal(str)  # 截图被点击
    
    def __init__(self, day: int, battle_data: Dict, items_db: Dict, parent=None):
        super().__init__(parent)
        self.day = day
        self.battle_data = battle_data
        self.items_db = items_db
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 标题：第X天
        title_label = QLabel(f"第 {self.day} 天")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;
                padding: 5px;
            }
        """)
        layout.addWidget(title_label)
        
        # 物品区域
        items_container = QWidget()
        items_layout = QHBoxLayout(items_container)
        items_layout.setContentsMargins(0, 0, 0, 0)
        items_layout.setSpacing(5)
        
        # 显示玩家物品 - 使用instance_id列表
        player_items = self.battle_data.get("player_items", [])
        for item in player_items:
            item_widget = self._create_item_widget(item)
            if item_widget:
                items_layout.addWidget(item_widget)
        
        items_layout.addStretch()
        layout.addWidget(items_container)
        
        # 截图区域
        screenshot_path = self.battle_data.get("screenshot")
        if screenshot_path:
            screenshot_widget = self._create_screenshot_widget(screenshot_path)
            layout.addWidget(screenshot_widget)
    
    def _create_item_widget(self, item_data: Dict) -> QWidget:
        """创建物品小部件 - 根据size调整宽度"""
        from gui.widgets.inline_item_label import InlineItemLabel
        from utils.image_loader import CardSize
        
        template_id = item_data.get("template_id", "unknown")
        
        # 从items_db获取物品信息（包括size）
        item_info = self.items_db.get(template_id, {})
        size = item_info.get("size", "medium")
        
        # 根据size确定CardSize
        if size == "small":
            card_size = CardSize.SMALL
        elif size == "large":
            card_size = CardSize.LARGE
        else:
            card_size = CardSize.MEDIUM
        
        # 创建物品标签（使用通用组件）
        try:
            item_widget = InlineItemLabel(
                item_id=template_id,
                tier_color="#555555",
                content_scale=1.0,
                card_size=card_size,
                clickable=False
            )
            return item_widget
        except Exception as e:
            print(f"创建物品部件失败: {template_id}, 错误: {e}")
            return None
    
    def _create_screenshot_widget(self, screenshot_path: str) -> QWidget:
        """创建截图部件"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 截图标签
        screenshot_label = QLabel()
        screenshot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        screenshot_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        screenshot_label.setStyleSheet("""
            QLabel {
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 3px;
                background-color: #1a1a1a;
            }
            QLabel:hover {
                border-color: rgba(255, 255, 255, 0.4);
            }
        """)
        
        # 加载图片
        pixmap = QPixmap(screenshot_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(400, 300, Qt.AspectRatioMode.KeepAspectRatio, 
                                         Qt.TransformationMode.SmoothTransformation)
            screenshot_label.setPixmap(scaled_pixmap)
            screenshot_label.setFixedSize(scaled_pixmap.size())
            
            # 点击事件
            screenshot_label.mousePressEvent = lambda e: self.screenshot_clicked.emit(screenshot_path)
        else:
            screenshot_label.setText("截图加载失败")
            screenshot_label.setFixedSize(400, 100)
        
        layout.addWidget(screenshot_label)
        
        return container


class MatchListItem(QWidget):
    """对局列表项"""
    
    def __init__(self, match_data: Dict, items_db: Dict, parent=None):
        super().__init__(parent)
        self.match_data = match_data
        self.items_db = items_db
        self.is_expanded = False
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 创建折叠标题
        self.header = self._create_header()
        self.main_layout.addWidget(self.header)
        
        # 创建详情容器（初始隐藏）
        self.details_container = QWidget()
        self.details_layout = QVBoxLayout(self.details_container)
        self.details_layout.setContentsMargins(15, 10, 15, 10)
        self.details_layout.setSpacing(10)
        
        self.details_container.setStyleSheet("""
            QWidget {
                background-color: rgba(30, 30, 30, 0.95);
            }
        """)
        
        self._create_details()
        self.details_container.hide()
        
        self.main_layout.addWidget(self.details_container)
    
    def _create_header(self) -> QWidget:
        """创建标题栏"""
        # 使用QWidget而不是QPushButton作为容器，避免按钮样式影响
        header = QWidget()
        header.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # 使标题栏可点击
        header.mousePressEvent = lambda e: self._toggle_expand()
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 15, 15, 15)
        header_layout.setSpacing(15)
        
        # 英雄头像
        hero_name = self.match_data.get("hero", "Unknown").lower()
        hero_avatar = QLabel()
        hero_avatar.setFixedSize(60, 60)
        hero_avatar.setScaledContents(True)
        
        # 加载英雄头像
        hero_image_path = f"assets/images/heroes/{hero_name}.webp"
        if os.path.exists(hero_image_path):
            pixmap = QPixmap(hero_image_path)
            if not pixmap.isNull():
                hero_avatar.setPixmap(pixmap)
        else:
            # 如果找不到头像，显示占位符
            hero_avatar.setText(hero_name[:1].upper())
            hero_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        hero_avatar.setStyleSheet("""
            QLabel {
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 30px;
                background-color: #1a1a1a;
                font-size: 24px;
                font-weight: bold;
                color: #ffffff;
            }
        """)
        header_layout.addWidget(hero_avatar)
        
        # 战绩符号区域
        results_widget = self._create_results_widget()
        header_layout.addWidget(results_widget)
        
        header_layout.addStretch()
        
        # 最终结果
        victory = self.match_data.get("victory", False)
        is_finished = self.match_data.get("is_finished", False)
        
        result_text = "胜利 ✓" if victory else "失败 ✗" if is_finished else "进行中..."
        result_color = "#4CAF50" if victory else "#F44336" if is_finished else "#FFA726"
        
        result_label = QLabel(result_text)
        result_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: bold;
                color: {result_color};
                padding: 5px 10px;
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 3px;
            }}
        """)
        header_layout.addWidget(result_label)
        
        # 展开指示器
        self.expand_indicator = QLabel("▼")
        self.expand_indicator.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #888888;
            }
        """)
        header_layout.addWidget(self.expand_indicator)
        
        # 样式
        header.setStyleSheet("""
            QWidget {
                background-color: rgba(45, 45, 45, 0.95);
                border-radius: 5px;
            }
            QWidget:hover {
                background-color: rgba(55, 55, 55, 0.95);
            }
        """)
        
        return header
    
    def _create_results_widget(self) -> QWidget:
        """创建战绩符号部件 - 两行显示，每行10个"""
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)
        
        # 获取PVP战斗记录
        pvp_battles = self.match_data.get("pvp_battles", [])
        total_days = len(pvp_battles)
        
        # 第一行：前10天
        row1 = QWidget()
        row1_layout = QHBoxLayout(row1)
        row1_layout.setContentsMargins(0, 0, 0, 0)
        row1_layout.setSpacing(3)
        
        for i in range(10):
            if i < total_days:
                # 有数据的天 - 使用真实的胜负信息
                battle = pvp_battles[i]
                victory = battle.get("victory")
                
                if victory is None:
                    # 没有胜负信息（旧数据）
                    symbol = "●"
                    color = "#888888"
                elif victory:
                    symbol = "✓"
                    color = "#4CAF50"
                else:
                    symbol = "✗"
                    color = "#F44336"
            else:
                # 空位
                symbol = "○"
                color = "#555555"
            
            label = QLabel(symbol)
            label.setFixedSize(20, 20)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(f"""
                QLabel {{
                    color: {color};
                    font-size: 14px;
                    font-weight: bold;
                }}
            """)
            row1_layout.addWidget(label)
        
        main_layout.addWidget(row1)
        
        # 第二行：后8天（11-18天）
        row2 = QWidget()
        row2_layout = QHBoxLayout(row2)
        row2_layout.setContentsMargins(0, 0, 0, 0)
        row2_layout.setSpacing(3)
        
        for i in range(10, 18):
            if i < total_days:
                # 有数据的天 - 使用真实的胜负信息
                battle = pvp_battles[i]
                victory = battle.get("victory")
                
                if victory is None:
                    # 没有胜负信息（旧数据）
                    symbol = "●"
                    color = "#888888"
                elif victory:
                    symbol = "✓"
                    color = "#4CAF50"
                else:
                    symbol = "✗"
                    color = "#F44336"
            else:
                # 空位
                symbol = "○"
                color = "#555555"
            
            label = QLabel(symbol)
            label.setFixedSize(20, 20)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(f"""
                QLabel {{
                    color: {color};
                    font-size: 14px;
                    font-weight: bold;
                }}
            """)
            row2_layout.addWidget(label)
        
        main_layout.addWidget(row2)
        
        return container
    
    def _create_details(self):
        """创建详情内容"""
        # 排序按钮
        sort_container = QWidget()
        sort_layout = QHBoxLayout(sort_container)
        sort_layout.setContentsMargins(0, 0, 0, 10)
        
        self.sort_btn = QPushButton("倒序排列")
        self.sort_btn.setFixedWidth(100)
        self.sort_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.sort_btn.clicked.connect(self._toggle_sort)
        self.sort_btn.setStyleSheet("""
            QPushButton {
                background-color: #555555;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #666666;
            }
        """)
        
        sort_layout.addWidget(self.sort_btn)
        sort_layout.addStretch()
        
        self.details_layout.addWidget(sort_container)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(300)  # ✅ 设置最小高度，确保内容可见
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # 天数列表容器
        self.days_container = QWidget()
        self.days_layout = QVBoxLayout(self.days_container)
        self.days_layout.setContentsMargins(0, 0, 0, 0)
        self.days_layout.setSpacing(10)
        
        self._populate_days(reverse=False)
        
        scroll_area.setWidget(self.days_container)
        self.details_layout.addWidget(scroll_area)
        
        self.is_reversed = False
    
    def _populate_days(self, reverse: bool = False):
        """填充天数数据"""
        # 清空现有内容
        while self.days_layout.count():
            item = self.days_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 获取PVP战斗记录
        pvp_battles = self.match_data.get("pvp_battles", [])
        
        # 排序
        if reverse:
            pvp_battles = list(reversed(pvp_battles))
        
        # 创建每天的卡片
        for battle in pvp_battles:
            day = battle.get("day", 0)
            day_card = DayBattleCard(day, battle, self.items_db)
            day_card.screenshot_clicked.connect(self._on_screenshot_clicked)
            self.days_layout.addWidget(day_card)
        
        self.days_layout.addStretch()
    
    def _toggle_sort(self):
        """切换排序"""
        self.is_reversed = not self.is_reversed
        self.sort_btn.setText("正序排列" if self.is_reversed else "倒序排列")
        self._populate_days(reverse=self.is_reversed)
    
    def _toggle_expand(self):
        """切换展开/折叠"""
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            self.details_container.show()
            self.expand_indicator.setText("▲")
        else:
            self.details_container.hide()
            self.expand_indicator.setText("▼")
    
    def _on_screenshot_clicked(self, screenshot_path: str):
        """截图被点击"""
        # 显示大图预览
        viewer = ImageViewer(screenshot_path, self)
        viewer.show()


class ImageViewer(QWidget):
    """图片查看器"""
    
    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        
        self.setWindowTitle("截图预览")
        self.setWindowFlags(Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 图片标签
        label = QLabel()
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("background-color: #1a1a1a;")
        
        # 加载图片
        pixmap = QPixmap(self.image_path)
        if not pixmap.isNull():
            # 缩放到合适大小（最大1200x800）
            scaled_pixmap = pixmap.scaled(1200, 800, Qt.AspectRatioMode.KeepAspectRatio,
                                         Qt.TransformationMode.SmoothTransformation)
            label.setPixmap(scaled_pixmap)
            self.resize(scaled_pixmap.size())
        else:
            label.setText("图片加载失败")
            self.resize(400, 300)
        
        layout.addWidget(label)
    
    def mousePressEvent(self, event):
        """点击关闭"""
        self.close()
