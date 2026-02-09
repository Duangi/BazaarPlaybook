"""
统一详情浮动窗 (Unified Detail Window)
- 根据识别类型（卡牌/技能/怪物）动态显示对应详情
- 点击空白处自动隐藏
- 支持快捷键唤起
- 可拖动，可缩放
"""
from typing import Optional, Literal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QPushButton)
from PySide6.QtCore import Qt, Signal, QTimer, QSettings, QPoint
from PySide6.QtGui import QCursor, QMouseEvent
from loguru import logger

from gui.widgets.item_detail_card import ItemDetailCard
from gui.widgets.monster_detail_content import MonsterDetailContent
from data_manager.monster_loader import Monster, MonsterDatabase
from gui.utils.frameless_helper import FramelessHelper
from gui.styles import COLOR_GOLD


DetailType = Literal["card", "skill", "monster"]


class UnifiedDetailWindow(QWidget):
    """
    统一详情窗口
    - 根据类型（card/skill/monster）动态加载对应详情组件
    - 失去焦点自动隐藏
    - 支持 ESC 关闭
    """
    
    closed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 窗口设置
        self.setWindowFlags(
            Qt.WindowType.Tool | 
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 加载设置
        self.settings = QSettings("Reborn", "UnifiedDetailWindow")
        self.content_scale = self.settings.value("scale", 1.0, type=float)
        self.content_scale = max(0.6, min(2.5, self.content_scale))
        
        # 当前显示的内容
        self.current_type: Optional[DetailType] = None
        self.current_id: Optional[str] = None
        self.current_widget: Optional[QWidget] = None
        
        # Monster Database
        self.monster_db = MonsterDatabase()
        
        # UI 初始化
        self._init_ui()
        
        # 拖动支持
        self.frameless = FramelessHelper(self, enable_drag=True, enable_resize=False)
        
        # 恢复位置
        pos = self.settings.value("pos")
        if pos and isinstance(pos, QPoint):
            self.move(pos)
        else:
            # 默认在鼠标附近
            cursor_pos = QCursor.pos()
            self.move(cursor_pos.x() + 20, cursor_pos.y() + 20)
    
    def _init_ui(self):
        """初始化 UI"""
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 容器框架
        self.container = QFrame()
        self.container.setObjectName("UnifiedDetailContainer")
        self.container.setStyleSheet(f"""
            #UnifiedDetailContainer {{
                background-color: rgba(15, 15, 20, 0.95);
                border: 2px solid {COLOR_GOLD};
                border-radius: 12px;
            }}
        """)
        self.main_layout.addWidget(self.container)
        
        # 容器内部布局
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)
        
        # 标题栏
        self._create_title_bar()
        
        # 内容区域
        self.content_layout = QVBoxLayout()
        m = int(10 * self.content_scale)
        self.content_layout.setContentsMargins(m, m, m, m)
        self.content_layout.setSpacing(0)
        self.container_layout.addLayout(self.content_layout)
        
        # 缩放控制按钮（右下角）
        self._create_scale_controls()
    
    def _create_title_bar(self):
        """创建标题栏"""
        title_bar = QFrame()
        title_bar.setObjectName("TitleBar")
        title_bar.setFixedHeight(36)
        title_bar.setStyleSheet(f"""
            #TitleBar {{
                background-color: rgba(30, 30, 35, 0.9);
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border-bottom: 1px solid {COLOR_GOLD};
            }}
        """)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(12, 0, 8, 0)
        
        # 标题文本
        self.title_label = QLabel("详情")
        self.title_label.setStyleSheet(f"""
            color: {COLOR_GOLD};
            font-size: 14px;
            font-weight: bold;
        """)
        title_layout.addWidget(self.title_label)
        
        title_layout.addStretch()
        
        # 关闭按钮
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: #999;
                border: none;
                border-radius: 14px;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
                color: {COLOR_GOLD};
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
        """)
        close_btn.clicked.connect(self.hide)
        title_layout.addWidget(close_btn)
        
        self.container_layout.addWidget(title_bar)
    
    def _create_scale_controls(self):
        """创建缩放控制按钮"""
        scale_widget = QWidget(self.container)
        scale_widget.setFixedSize(80, 32)
        
        scale_layout = QHBoxLayout(scale_widget)
        scale_layout.setContentsMargins(4, 4, 4, 4)
        scale_layout.setSpacing(4)
        
        btn_style = f"""
            QPushButton {{
                background-color: {COLOR_GOLD};
                color: #000;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: #ffd700;
            }}
            QPushButton:pressed {{
                background-color: #b8860b;
            }}
        """
        
        # 减小按钮
        minus_btn = QPushButton("−")
        minus_btn.setFixedSize(24, 24)
        minus_btn.setStyleSheet(btn_style)
        minus_btn.clicked.connect(lambda: self._change_scale(-0.1))
        scale_layout.addWidget(minus_btn)
        
        # 缩放值显示
        self.scale_value_label = QLabel(f"{int(self.content_scale * 100)}%")
        self.scale_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scale_value_label.setStyleSheet(f"""
            color: {COLOR_GOLD};
            font-size: 11px;
            font-weight: bold;
        """)
        scale_layout.addWidget(self.scale_value_label)
        
        # 增大按钮
        plus_btn = QPushButton("+")
        plus_btn.setFixedSize(24, 24)
        plus_btn.setStyleSheet(btn_style)
        plus_btn.clicked.connect(lambda: self._change_scale(0.1))
        scale_layout.addWidget(plus_btn)
        
        # 定位到右下角（在 resizeEvent 中更新）
        self.scale_controls = scale_widget
        self.scale_controls.raise_()
    
    def _change_scale(self, delta: float):
        """改变缩放比例"""
        new_scale = self.content_scale + delta
        new_scale = max(0.6, min(2.5, new_scale))
        
        if new_scale != self.content_scale:
            self.content_scale = new_scale
            self.settings.setValue("scale", self.content_scale)
            self.scale_value_label.setText(f"{int(self.content_scale * 100)}%")
            
            # 重新显示当前内容以应用新缩放
            if self.current_type and self.current_id:
                self._reload_content()
    
    def show_detail(self, detail_type: DetailType, detail_id: str):
        """
        显示详情
        Args:
            detail_type: 详情类型 ('card', 'skill', 'monster')
            detail_id: 物品/怪物 ID
        """
        # 如果是相同内容且已显示，只需提升窗口
        if (detail_type == self.current_type and 
            detail_id == self.current_id and 
            self.isVisible()):
            self.raise_()
            self.activateWindow()
            return
        
        # 保存当前内容信息
        self.current_type = detail_type
        self.current_id = detail_id
        
        # 更新标题
        if detail_type == "monster":
            self.title_label.setText("怪物详情")
        elif detail_type == "skill":
            self.title_label.setText("技能详情")
        else:
            self.title_label.setText("卡牌详情")
        
        # 清空旧内容
        self._clear_content()
        
        # 加载新内容
        self._load_content(detail_type, detail_id)
        
        # 调整大小
        self._adjust_size()
        
        # 显示窗口
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus()
    
    def _load_content(self, detail_type: DetailType, detail_id: str):
        """加载内容组件"""
        try:
            if detail_type == "monster":
                # 加载怪物详情
                monster = self.monster_db.get_monster_by_id(detail_id)
                if monster:
                    self.current_widget = MonsterDetailContent()
                    self.current_widget.setStyleSheet("background: transparent;")
                    self.current_widget.set_monster(monster)
                else:
                    logger.warning(f"Monster not found: {detail_id}")
                    self._show_error("未找到怪物信息")
                    return
            
            elif detail_type in ["card", "skill"]:
                # 加载卡牌/技能详情
                self.current_widget = ItemDetailCard(
                    item_id=detail_id,
                    item_type=detail_type,
                    default_expanded=True,
                    enable_tier_click=True,
                    content_scale=self.content_scale
                )
                self.current_widget.setStyleSheet("background: transparent;")
            
            else:
                logger.error(f"Unknown detail type: {detail_type}")
                self._show_error("未知类型")
                return
            
            if self.current_widget:
                self.content_layout.addWidget(self.current_widget)
        
        except Exception as e:
            logger.error(f"Failed to load content: {e}")
            self._show_error(f"加载失败: {e}")
    
    def _show_error(self, message: str):
        """显示错误信息"""
        error_label = QLabel(message)
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("""
            color: #ff4444;
            font-size: 14px;
            padding: 30px;
        """)
        self.content_layout.addWidget(error_label)
        self.current_widget = error_label
    
    def _clear_content(self):
        """清空内容区域"""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.current_widget = None
    
    def _reload_content(self):
        """重新加载当前内容（应用新缩放）"""
        if self.current_type and self.current_id:
            # 清空并重新加载
            self._clear_content()
            self._load_content(self.current_type, self.current_id)
            self._adjust_size()
    
    def _adjust_size(self):
        """调整窗口大小以适应内容"""
        from PySide6.QtWidgets import QApplication
        
        # 处理事件以让布局更新
        QApplication.processEvents()
        
        # 根据内容类型设置合适的宽度
        if self.current_type == "monster":
            base_width = 450
        else:
            base_width = 320
        
        target_width = int(base_width * self.content_scale)
        
        # 设置固定宽度，让高度自适应
        self.setFixedWidth(target_width)
        
        # 获取内容建议高度
        QApplication.processEvents()
        content_height = self.container.sizeHint().height()
        
        # 限制最大高度（避免超出屏幕）
        max_height = 800
        final_height = min(content_height, max_height)
        
        self.setFixedHeight(final_height)
        
        # 更新缩放控件位置
        self._update_scale_controls_pos()
    
    def resizeEvent(self, event):
        """窗口大小改变时更新控件位置"""
        super().resizeEvent(event)
        self._update_scale_controls_pos()
    
    def _update_scale_controls_pos(self):
        """更新缩放控件位置（右下角）"""
        if hasattr(self, 'scale_controls'):
            margin = 8
            x = self.width() - self.scale_controls.width() - margin
            y = self.height() - self.scale_controls.height() - margin
            self.scale_controls.move(x, y)
    
    def changeEvent(self, event):
        """窗口激活状态改变"""
        if event.type() == event.Type.ActivationChange:
            if not self.isActiveWindow() and self.isVisible():
                # 失去焦点时隐藏
                self.hide()
        super().changeEvent(event)
    
    def keyPressEvent(self, event):
        """按键事件 - ESC 关闭"""
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        super().keyPressEvent(event)
    
    def hideEvent(self, event):
        """隐藏时保存位置"""
        self.settings.setValue("pos", self.pos())
        self.closed.emit()
        super().hideEvent(event)
    
    def closeEvent(self, event):
        """关闭时保存设置"""
        self.settings.setValue("pos", self.pos())
        self.settings.setValue("scale", self.content_scale)
        super().closeEvent(event)
    
    def mouseReleaseEvent(self, event):
        """拖动结束时保存位置"""
        super().mouseReleaseEvent(event)
        self.settings.setValue("pos", self.pos())
