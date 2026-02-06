"""
侧滑副屏组件 (Drawer Panel)
支持左右两个方向的滑入/滑出动画
"""
from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame, QPushButton
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Signal, QRect, QTimer
from PySide6.QtGui import QPainter, QColor


class DrawerPanel(QWidget):
    """
    侧滑副屏组件
    - 支持从左侧或右侧滑入
    - 带滑入/滑出动画
    - 磨砂黑半透明背景
    - 与主窗口之间有金色分割线
    """
    
    closed = Signal()  # 关闭信号
    
    def __init__(self, parent: QWidget, direction: str = "left"):
        """
        Args:
            parent: 父窗口
            direction: 滑入方向 "left" (从左侧滑入) 或 "right" (从右侧滑入)
        """
        super().__init__(parent)
        self.parent_widget = parent
        self.direction = direction
        self.drawer_width = 400  # 副屏宽度
        self.is_visible = False
        
        # 延迟关闭定时器（鼠标离开后延迟隐藏）
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.setInterval(300)  # 300ms 延迟
        self.hide_timer.timeout.connect(self._delayed_hide)
        
        self.setMouseTracking(True)
        
        self._init_ui()
        self._init_animation()
        
        # 初始化时隐藏
        self.hide()
    
    def _init_ui(self):
        """初始化UI"""
        self.setObjectName("DrawerPanel")
        
        # 根布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 主容器（带金色分割线）
        self.main_container = QFrame()
        self.main_container.setObjectName("DrawerContainer")
        layout.addWidget(self.main_container)
        
        # 主容器布局
        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(15, 15, 15, 15)
        container_layout.setSpacing(12)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(15)
        
        scroll.setWidget(self.content_widget)
        container_layout.addWidget(scroll)
        
        self._setup_style()
    
    def _setup_style(self):
        """设置样式"""
        # 根据方向设置分割线位置
        if self.direction == "left":
            border_style = "border-right: 2px solid #f59e0b;"
        else:
            border_style = "border-left: 2px solid #f59e0b;"
        
        self.main_container.setStyleSheet(f"""
            #DrawerContainer {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(10, 10, 12, 0.95),
                    stop:1 rgba(5, 5, 8, 0.95));
                {border_style}
                backdrop-filter: blur(10px);
            }}
        """)
    
    def _init_animation(self):
        """初始化滑入/滑出动画"""
        self.slide_anim = QPropertyAnimation(self, b"geometry")
        self.slide_anim.setDuration(300)
        self.slide_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def show_drawer(self):
        """显示副屏（滑入）"""
        if self.is_visible:
            return
        
        self.is_visible = True
        self.show()
        self.raise_()
        
        # 获取父窗口尺寸
        parent_rect = self.parent_widget.rect()
        
        # 计算起始和结束位置
        if self.direction == "left":
            # 从左侧滑入
            start_rect = QRect(-self.drawer_width, 0, self.drawer_width, parent_rect.height())
            end_rect = QRect(0, 0, self.drawer_width, parent_rect.height())
        else:
            # 从右侧滑入
            start_rect = QRect(parent_rect.width(), 0, self.drawer_width, parent_rect.height())
            end_rect = QRect(parent_rect.width() - self.drawer_width, 0, self.drawer_width, parent_rect.height())
        
        # 设置起始位置并播放动画
        self.setGeometry(start_rect)
        self.slide_anim.setStartValue(start_rect)
        self.slide_anim.setEndValue(end_rect)
        self.slide_anim.start()
    
    def hide_drawer(self):
        """隐藏副屏（滑出） - 启动延迟定时器"""
        if not self.is_visible:
            return
        
        # 启动延迟定时器
        self.hide_timer.start()
    
    def _delayed_hide(self):
        """延迟隐藏（定时器触发）"""
        if not self.is_visible:
            return
        
        self.is_visible = False
        
        # 获取父窗口尺寸
        parent_rect = self.parent_widget.rect()
        current_rect = self.geometry()
        
        # 计算结束位置（滑出到屏幕外）
        if self.direction == "left":
            end_rect = QRect(-self.drawer_width, 0, self.drawer_width, parent_rect.height())
        else:
            end_rect = QRect(parent_rect.width(), 0, self.drawer_width, parent_rect.height())
        
        # 播放动画
        self.slide_anim.setStartValue(current_rect)
        self.slide_anim.setEndValue(end_rect)
        self.slide_anim.finished.connect(self._on_hide_finished)
        self.slide_anim.start()
    
    def enterEvent(self, event):
        """鼠标进入抽屉 - 取消隐藏定时器"""
        self.hide_timer.stop()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开抽屉 - 启动延迟隐藏"""
        if self.is_visible:
            self.hide_timer.start()
        super().leaveEvent(event)
    
    def _on_hide_finished(self):
        """隐藏动画完成"""
        self.hide()
        self.closed.emit()
        self.slide_anim.finished.disconnect(self._on_hide_finished)
    
    def toggle_drawer(self):
        """切换显示/隐藏"""
        if self.is_visible:
            self.hide_drawer()
        else:
            self.show_drawer()
    
    def set_content(self, widget: QWidget):
        """
        设置副屏内容
        Args:
            widget: 要显示的内容组件
        """
        # 清空旧内容
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 添加新内容
        self.content_layout.addWidget(widget)
    
    def clear_content(self):
        """清空内容"""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def update_position(self):
        """更新位置（在父窗口大小改变时调用）"""
        if not self.is_visible:
            return
        
        parent_rect = self.parent_widget.rect()
        
        if self.direction == "left":
            self.setGeometry(0, 0, self.drawer_width, parent_rect.height())
        else:
            self.setGeometry(parent_rect.width() - self.drawer_width, 0, self.drawer_width, parent_rect.height())
    
    @staticmethod
    def auto_direction(parent_widget: QWidget) -> str:
        """
        根据父窗口在屏幕上的位置自动选择滑入方向
        Args:
            parent_widget: 父窗口
        Returns:
            "left" 或 "right"
        """
        from PySide6.QtWidgets import QApplication
        
        # 获取屏幕几何信息
        screen = QApplication.primaryScreen().geometry()
        window_center = parent_widget.mapToGlobal(parent_widget.rect().center())
        
        # 如果窗口中心在屏幕左半部分，向右滑入；否则向左滑入
        if window_center.x() < screen.width() / 2:
            return "right"
        else:
            return "left"
