"""
无边框窗口助手类 (Frameless Window Helper)
提供拖拽和调整大小功能，无需修改窗口继承关系

使用方法：
    class MyWindow(QWidget):
        def __init__(self):
            super().__init__()
            self.helper = FramelessHelper(self, margin=8, snap_to_top=True)
            self.setMinimumSize(300, 400)
"""

from PySide6.QtCore import Qt, QPoint, QRect, QObject, QEvent
from PySide6.QtGui import QCursor


class FramelessHelper(QObject):
    """
    无边框窗口助手
    
    通过事件过滤器自动为任何窗口添加拖拽和调整大小功能
    """
    
    # 定义边缘常量
    EDGE_NONE = 0
    EDGE_LEFT = 1
    EDGE_RIGHT = 2
    EDGE_TOP = 4
    EDGE_BOTTOM = 8
    EDGE_TOPLEFT = EDGE_TOP | EDGE_LEFT
    EDGE_TOPRIGHT = EDGE_TOP | EDGE_RIGHT
    EDGE_BOTTOMLEFT = EDGE_BOTTOM | EDGE_LEFT
    EDGE_BOTTOMRIGHT = EDGE_BOTTOM | EDGE_RIGHT
    
    def __init__(self, target_widget, margin=8, snap_to_top=True, 
                 enable_drag=True, enable_resize=True, debug=False):
        """
        初始化助手
        
        Args:
            target_widget: 目标窗口（必须是 QWidget 或其子类）
            margin: 边缘检测区域宽度（像素）
            snap_to_top: 是否启用顶部吸附
            enable_drag: 是否启用拖拽
            enable_resize: 是否启用调整大小
            debug: 是否启用调试输出
        """
        super().__init__(target_widget)
        self.target = target_widget
        self.margin = margin
        self.snap_to_top = snap_to_top
        self.enable_drag = enable_drag
        self.enable_resize = enable_resize
        self.debug = debug
        
        # 状态标志
        self.is_dragging = False
        self.is_resizing = False
        self.drag_pos = QPoint()
        self.resize_edge = self.EDGE_NONE
        self.resize_start_geometry = QRect()
        
        # 启用鼠标追踪（用于改变光标形状）
        self.target.setMouseTracking(True)
        # 启用 Hover 事件（鼠标悬停）
        self.target.setAttribute(Qt.WA_Hover, True)
        
        # 安装事件过滤器，接管目标窗口的鼠标事件
        self.target.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """
        事件过滤器 - 拦截并处理鼠标事件
        返回 False 让事件继续传递给子控件（如按钮）
        """
        if obj != self.target:
            return False
        
        event_type = event.type()
        
        if event_type == QEvent.Type.MouseButtonPress:
            self._handle_press(event)
        elif event_type == QEvent.Type.MouseMove:
            self._handle_move(event)
        elif event_type == QEvent.Type.HoverMove:
            # Hover 移动（没有按键时）
            if not self.is_resizing and not self.is_dragging:
                edge = self._get_edge(event.pos())
                self._update_cursor(edge)
        elif event_type == QEvent.Type.MouseButtonRelease:
            self._handle_release(event)
        elif event_type == QEvent.Type.Leave:
            # 鼠标离开窗口时恢复默认光标
            self.target.setCursor(Qt.ArrowCursor)
        
        # 返回 False 让事件继续传递
        return False
    
    def _get_edge(self, pos):
        """
        检测鼠标位置在窗口的哪个边缘
        
        Args:
            pos: 鼠标位置（窗口相对坐标）
        
        Returns:
            int: 边缘标识（使用位运算组合多个方向）
        """
        rect = self.target.rect()
        x, y = pos.x(), pos.y()
        m = self.margin
        
        edge = self.EDGE_NONE
        
        # 检测左右边缘
        if x < m:
            edge |= self.EDGE_LEFT
        elif x > rect.width() - m:
            edge |= self.EDGE_RIGHT
        
        # 检测上下边缘
        if y < m:
            edge |= self.EDGE_TOP
        elif y > rect.height() - m:
            edge |= self.EDGE_BOTTOM
        
        if self.debug and edge != self.EDGE_NONE:
            edge_names = []
            if edge & self.EDGE_LEFT: edge_names.append("LEFT")
            if edge & self.EDGE_RIGHT: edge_names.append("RIGHT")
            if edge & self.EDGE_TOP: edge_names.append("TOP")
            if edge & self.EDGE_BOTTOM: edge_names.append("BOTTOM")
            print(f"[FramelessHelper] Edge detected: {' | '.join(edge_names)} at ({x}, {y})")
        
        return edge
    
    def _update_cursor(self, edge):
        """
        根据边缘位置改变光标形状
        
        Args:
            edge: 边缘标识
        """
        if not self.enable_resize:
            self.target.setCursor(Qt.ArrowCursor)
            return
        
        cursor = Qt.ArrowCursor  # 默认箭头
        
        # 左右边缘
        if edge in [self.EDGE_LEFT, self.EDGE_RIGHT]:
            cursor = Qt.SizeHorCursor
        # 上下边缘
        elif edge in [self.EDGE_TOP, self.EDGE_BOTTOM]:
            cursor = Qt.SizeVerCursor
        # 左上角和右下角（对角线 \）
        elif edge in [self.EDGE_TOPLEFT, self.EDGE_BOTTOMRIGHT]:
            cursor = Qt.SizeFDiagCursor
        # 右上角和左下角（对角线 /）
        elif edge in [self.EDGE_TOPRIGHT, self.EDGE_BOTTOMLEFT]:
            cursor = Qt.SizeBDiagCursor
        
        if self.debug and cursor != Qt.ArrowCursor:
            cursor_names = {
                Qt.SizeHorCursor: "Horizontal",
                Qt.SizeVerCursor: "Vertical",
                Qt.SizeFDiagCursor: "Diagonal \\",
                Qt.SizeBDiagCursor: "Diagonal /"
            }
            print(f"[FramelessHelper] Cursor changed to: {cursor_names.get(cursor, 'Unknown')}")
        
        self.target.setCursor(cursor)
    
    def _handle_press(self, event):
        """处理鼠标按下事件"""
        if event.button() != Qt.LeftButton:
            return
        
        edge = self._get_edge(event.pos())
        
        # 优先处理调整大小（在边缘区域）
        if edge != self.EDGE_NONE and self.enable_resize:
            self.is_resizing = True
            self.resize_edge = edge
            self.resize_start_geometry = self.target.geometry()
        # 否则处理拖拽（在中央区域）
        elif self.enable_drag:
            self.is_dragging = True
            self.drag_pos = event.globalPosition().toPoint() - self.target.pos()
    
    def _handle_move(self, event):
        """处理鼠标移动事件"""
        # 如果没有按下左键，只更新光标形状
        if not self.is_resizing and not self.is_dragging:
            edge = self._get_edge(event.pos())
            self._update_cursor(edge)
            return
        
        # 正在调整大小
        if self.is_resizing:
            self._do_resize(event.globalPosition().toPoint())
        # 正在拖拽
        elif self.is_dragging:
            new_pos = event.globalPosition().toPoint() - self.drag_pos
            
            # 顶部吸附逻辑
            if self.snap_to_top and new_pos.y() < 30:
                new_pos.setY(0)
            
            self.target.move(new_pos)
    
    def _do_resize(self, global_pos):
        """
        执行调整大小操作
        
        Args:
            global_pos: 鼠标的全局坐标
        """
        geo = QRect(self.resize_start_geometry)
        
        # 根据边缘方向调整几何形状
        if self.resize_edge & self.EDGE_LEFT:
            geo.setLeft(global_pos.x())
        if self.resize_edge & self.EDGE_RIGHT:
            geo.setRight(global_pos.x())
        if self.resize_edge & self.EDGE_TOP:
            geo.setTop(global_pos.y())
        if self.resize_edge & self.EDGE_BOTTOM:
            geo.setBottom(global_pos.y())
        
        # 限制最小和最大尺寸
        min_w = self.target.minimumWidth()
        min_h = self.target.minimumHeight()
        max_w = self.target.maximumWidth()
        max_h = self.target.maximumHeight()
        
        # 检查最小尺寸
        if geo.width() < min_w or geo.height() < min_h:
            return
        
        # 检查最大尺寸（16777215 是 Qt 的默认最大值，表示没有限制）
        if (max_w < 16777215 and geo.width() > max_w) or (max_h < 16777215 and geo.height() > max_h):
            return
        
        # 应用新的几何形状
        self.target.setGeometry(geo)
    
    def _handle_release(self, event):
        """处理鼠标释放事件"""
        self.is_dragging = False
        self.is_resizing = False
        self.resize_edge = self.EDGE_NONE
        self.target.setCursor(Qt.ArrowCursor)
    
    def set_snap_to_top(self, enabled):
        """动态设置顶部吸附功能"""
        self.snap_to_top = enabled
    
    def set_margin(self, margin):
        """动态设置边缘检测区域宽度"""
        self.margin = margin
    
    def set_draggable(self, enabled):
        """动态设置是否可拖拽"""
        self.enable_drag = enabled
    
    def set_resizable(self, enabled):
        """动态设置是否可调整大小"""
        self.enable_resize = enabled
        if not enabled:
            self.target.setCursor(Qt.ArrowCursor)
