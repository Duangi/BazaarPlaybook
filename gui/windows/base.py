# gui/windows/base.py
"""
窗口功能混入类（Mixin）
使用方法：class MyWindow(QWidget, DraggableMixin, ResizableMixin)
"""
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPoint, QRect
from PySide6.QtGui import QCursor


class DraggableMixin:
    """
    可拖拽功能混入
    为窗口添加全窗口拖动和顶部吸附功能
    
    使用方法：
        class MyWindow(QWidget, DraggableMixin):
            def __init__(self):
                super().__init__()
                self.setup_draggable(snap_to_top=True)
    """
    def setup_draggable(self, snap_to_top=True):
        """
        启用拖拽功能
        
        Args:
            snap_to_top: 是否启用顶部吸附
        """
        self._drag_snap_to_top = snap_to_top
        self._drag_is_dragging = False
        self._drag_offset = QPoint()
    
    def _handle_drag_press(self, event):
        """处理拖拽的按下事件，返回 True 表示已处理"""
        if event.button() == Qt.LeftButton:
            self._drag_is_dragging = True
            self._drag_offset = event.globalPosition().toPoint() - self.pos()
            return True
        return False

    def _handle_drag_move(self, event):
        """处理拖拽的移动事件，返回 True 表示已处理"""
        if self._drag_is_dragging:
            new_pos = event.globalPosition().toPoint() - self._drag_offset
            
            # 执行顶部吸附逻辑
            if self._drag_snap_to_top and new_pos.y() < 30:
                new_pos.setY(0)
                
            self.move(new_pos)
            return True
        return False

    def _handle_drag_release(self, event):
        """处理拖拽的释放事件，返回 True 表示已处理"""
        if self._drag_is_dragging:
            self._drag_is_dragging = False
            return True
        return False


class ResizableMixin:
    """
    可调整大小功能混入
    为窗口添加边缘拖拽调整大小的功能
    
    使用方法：
        class MyWindow(QWidget, ResizableMixin):
            def __init__(self):
                super().__init__()
                self.setup_resizable(
                    min_width=300, min_height=400,
                    max_width=1200, max_height=900,
                    resize_margin=8
                )
    """
    # 边缘标识
    EDGE_NONE = 0
    EDGE_LEFT = 1
    EDGE_RIGHT = 2
    EDGE_TOP = 4
    EDGE_BOTTOM = 8
    EDGE_TOPLEFT = EDGE_TOP | EDGE_LEFT
    EDGE_TOPRIGHT = EDGE_TOP | EDGE_RIGHT
    EDGE_BOTTOMLEFT = EDGE_BOTTOM | EDGE_LEFT
    EDGE_BOTTOMRIGHT = EDGE_BOTTOM | EDGE_RIGHT
    
    def setup_resizable(self, min_width=200, min_height=200, 
                       max_width=2000, max_height=2000, 
                       resize_margin=8):
        """
        启用调整大小功能
        
        Args:
            min_width: 最小宽度
            min_height: 最小高度
            max_width: 最大宽度
            max_height: 最大高度
            resize_margin: 边缘检测区域宽度（像素）
        """
        self._resize_min_width = min_width
        self._resize_min_height = min_height
        self._resize_max_width = max_width
        self._resize_max_height = max_height
        self._resize_margin = resize_margin
        self._resize_edge = self.EDGE_NONE
        self._resize_is_resizing = False
        self._resize_start_pos = QPoint()
        self._resize_start_geometry = QRect()
        
        # 启用鼠标追踪以更新光标
        self.setMouseTracking(True)
    
    def _get_resize_edge(self, pos):
        """
        检测鼠标位置在哪个边缘
        
        Args:
            pos: 鼠标位置（窗口相对坐标）
            
        Returns:
            int: 边缘标识
        """
        rect = self.rect()
        margin = self._resize_margin
        edge = self.EDGE_NONE
        
        # 检测左右边缘
        if pos.x() <= margin:
            edge |= self.EDGE_LEFT
        elif pos.x() >= rect.width() - margin:
            edge |= self.EDGE_RIGHT
            
        # 检测上下边缘
        if pos.y() <= margin:
            edge |= self.EDGE_TOP
        elif pos.y() >= rect.height() - margin:
            edge |= self.EDGE_BOTTOM
            
        return edge
    
    def _update_resize_cursor(self, edge):
        """
        根据边缘位置更新光标样式
        
        Args:
            edge: 边缘标识
        """
        cursor_map = {
            self.EDGE_LEFT: Qt.SizeHorCursor,
            self.EDGE_RIGHT: Qt.SizeHorCursor,
            self.EDGE_TOP: Qt.SizeVerCursor,
            self.EDGE_BOTTOM: Qt.SizeVerCursor,
            self.EDGE_TOPLEFT: Qt.SizeFDiagCursor,
            self.EDGE_TOPRIGHT: Qt.SizeBDiagCursor,
            self.EDGE_BOTTOMLEFT: Qt.SizeBDiagCursor,
            self.EDGE_BOTTOMRIGHT: Qt.SizeFDiagCursor,
        }
        
        if edge in cursor_map:
            self.setCursor(cursor_map[edge])
        else:
            self.unsetCursor()
    
    def _handle_resize_press(self, event):
        """处理调整大小的按下事件，返回 True 表示已处理"""
        if event.button() == Qt.LeftButton:
            self._resize_edge = self._get_resize_edge(event.pos())
            
            if self._resize_edge != self.EDGE_NONE:
                self._resize_is_resizing = True
                self._resize_start_pos = event.globalPosition().toPoint()
                self._resize_start_geometry = self.geometry()
                return True
        return False
    
    def _handle_resize_move(self, event):
        """处理调整大小的移动事件，返回 True 表示已处理"""
        if self._resize_is_resizing:
            # 正在调整大小
            delta = event.globalPosition().toPoint() - self._resize_start_pos
            new_geo = QRect(self._resize_start_geometry)
            
            # 根据边缘调整几何形状
            if self._resize_edge & self.EDGE_LEFT:
                new_geo.setLeft(new_geo.left() + delta.x())
            if self._resize_edge & self.EDGE_RIGHT:
                new_geo.setRight(new_geo.right() + delta.x())
            if self._resize_edge & self.EDGE_TOP:
                new_geo.setTop(new_geo.top() + delta.y())
            if self._resize_edge & self.EDGE_BOTTOM:
                new_geo.setBottom(new_geo.bottom() + delta.y())
            
            # 应用尺寸限制
            if new_geo.width() < self._resize_min_width:
                if self._resize_edge & self.EDGE_LEFT:
                    new_geo.setLeft(new_geo.right() - self._resize_min_width)
                else:
                    new_geo.setWidth(self._resize_min_width)
                    
            if new_geo.width() > self._resize_max_width:
                if self._resize_edge & self.EDGE_LEFT:
                    new_geo.setLeft(new_geo.right() - self._resize_max_width)
                else:
                    new_geo.setWidth(self._resize_max_width)
                    
            if new_geo.height() < self._resize_min_height:
                if self._resize_edge & self.EDGE_TOP:
                    new_geo.setTop(new_geo.bottom() - self._resize_min_height)
                else:
                    new_geo.setHeight(self._resize_min_height)
                    
            if new_geo.height() > self._resize_max_height:
                if self._resize_edge & self.EDGE_TOP:
                    new_geo.setTop(new_geo.bottom() - self._resize_max_height)
                else:
                    new_geo.setHeight(self._resize_max_height)
            
            self.setGeometry(new_geo)
            return True
        else:
            # 更新光标（悬停检测）
            edge = self._get_resize_edge(event.pos())
            self._update_resize_cursor(edge)
        
        return False
    
    def _handle_resize_release(self, event):
        """处理调整大小的释放事件，返回 True 表示已处理"""
        if self._resize_is_resizing:
            self._resize_is_resizing = False
            self._resize_edge = self.EDGE_NONE
            return True
        return False


class WindowMixin(DraggableMixin, ResizableMixin):
    """
    组合型窗口 Mixin - 同时支持拖拽和调整大小
    自动处理事件冲突
    
    使用方法：
        class MyWindow(QWidget, WindowMixin):
            def __init__(self):
                super().__init__()
                self.setup_window_features(
                    draggable=True,
                    resizable=True,
                    snap_to_top=True,
                    min_width=400,
                    min_height=300
                )
    """
    def setup_window_features(self, draggable=True, resizable=True, 
                             snap_to_top=True, min_width=200, min_height=200,
                             max_width=2000, max_height=2000, resize_margin=8):
        """
        一次性设置窗口的拖拽和调整大小功能
        
        Args:
            draggable: 是否启用拖拽
            resizable: 是否启用调整大小
            其他参数同各自的 setup 方法
        """
        self._window_draggable = draggable
        self._window_resizable = resizable
        
        if draggable:
            self.setup_draggable(snap_to_top=snap_to_top)
        if resizable:
            self.setup_resizable(min_width, min_height, max_width, max_height, resize_margin)
    
    def mousePressEvent(self, event):
        """统一的鼠标按下事件处理"""
        # 优先检查调整大小（边缘区域）
        if self._window_resizable and self._handle_resize_press(event):
            event.accept()
            return
        
        # 再检查拖拽（中央区域）
        if self._window_draggable and self._handle_drag_press(event):
            event.accept()
            return
        
        # 传递给父类
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """统一的鼠标移动事件处理"""
        # 优先处理调整大小
        if self._window_resizable and self._handle_resize_move(event):
            event.accept()
            return
        
        # 再处理拖拽
        if self._window_draggable and self._handle_drag_move(event):
            event.accept()
            return
        
        # 传递给父类
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """统一的鼠标释放事件处理"""
        # 处理调整大小释放
        if self._window_resizable and self._handle_resize_release(event):
            event.accept()
        
        # 处理拖拽释放
        if self._window_draggable and self._handle_drag_release(event):
            event.accept()
        
        # 传递给父类
        super().mouseReleaseEvent(event)


class DraggableWindow(QWidget, DraggableMixin):
    """
    保留向后兼容的基类
    推荐使用 WindowMixin：class MyWindow(QWidget, WindowMixin)
    """
    def __init__(self, snap_to_top=True):
        super().__init__()
        self.setup_draggable(snap_to_top=snap_to_top)
    
    def mousePressEvent(self, event):
        if not self._handle_drag_press(event):
            super().mousePressEvent(event)
        else:
            event.accept()
    
    def mouseMoveEvent(self, event):
        if not self._handle_drag_move(event):
            super().mouseMoveEvent(event)
        else:
            event.accept()
    
    def mouseReleaseEvent(self, event):
        if not self._handle_drag_release(event):
            super().mouseReleaseEvent(event)
        else:
            event.accept()

    """
    可拖拽功能混入
    为窗口添加全窗口拖动和顶部吸附功能
    
    使用方法：
        class MyWindow(QWidget, DraggableMixin):
            def __init__(self):
                super().__init__()
                self.setup_draggable(snap_to_top=True)
    """
    def setup_draggable(self, snap_to_top=True):
        """
        启用拖拽功能
        
        Args:
            snap_to_top: 是否启用顶部吸附
        """
        self._snap_to_top = snap_to_top
        self._is_dragging = False
        self._drag_offset = QPoint()
    
    def mousePressEvent(self, event):
        """重写鼠标按下事件"""
        # 检查是否在调整大小区域（如果同时使用了 ResizableMixin）
        if hasattr(self, '_resize_edge'):
            edge = self._get_resize_edge(event.pos())
            if edge != 0:  # 在调整大小区域，不处理拖拽
                if hasattr(super(), 'mousePressEvent'):
                    super().mousePressEvent(event)
                return
        
        # 处理拖拽
        if event.button() == Qt.LeftButton and hasattr(self, '_is_dragging'):
            self._is_dragging = True
            self._drag_offset = event.globalPosition().toPoint() - self.pos()
            event.accept()
            return
        
        # 传递给其他处理器
        if hasattr(super(), 'mousePressEvent'):
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """重写鼠标移动事件"""
        # 先处理拖拽
        if hasattr(self, '_is_dragging') and self._is_dragging:
            new_pos = event.globalPosition().toPoint() - self._drag_offset
            
            # 执行顶部吸附逻辑
            if self._snap_to_top and new_pos.y() < 30:
                new_pos.setY(0)
                
            self.move(new_pos)
            event.accept()
            return
        
        # 传递给其他处理器（例如 ResizableMixin）
        if hasattr(super(), 'mouseMoveEvent'):
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """重写鼠标释放事件"""
        if hasattr(self, '_is_dragging') and self._is_dragging:
            self._is_dragging = False
            event.accept()
        
        # 传递给其他处理器
        if hasattr(super(), 'mouseReleaseEvent'):
            super().mouseReleaseEvent(event)


class ResizableMixin:
    """
    可调整大小功能混入
    为窗口添加边缘拖拽调整大小的功能
    
    使用方法：
        class MyWindow(QWidget, ResizableMixin):
            def __init__(self):
                super().__init__()
                self.setup_resizable(
                    min_width=300, min_height=400,
                    max_width=1200, max_height=900,
                    resize_margin=8
                )
    """
    # 边缘标识
    EDGE_NONE = 0
    EDGE_LEFT = 1
    EDGE_RIGHT = 2
    EDGE_TOP = 4
    EDGE_BOTTOM = 8
    EDGE_TOPLEFT = EDGE_TOP | EDGE_LEFT
    EDGE_TOPRIGHT = EDGE_TOP | EDGE_RIGHT
    EDGE_BOTTOMLEFT = EDGE_BOTTOM | EDGE_LEFT
    EDGE_BOTTOMRIGHT = EDGE_BOTTOM | EDGE_RIGHT
    
    def setup_resizable(self, min_width=200, min_height=200, 
                       max_width=2000, max_height=2000, 
                       resize_margin=8):
        """
        启用调整大小功能
        
        Args:
            min_width: 最小宽度
            min_height: 最小高度
            max_width: 最大宽度
            max_height: 最大高度
            resize_margin: 边缘检测区域宽度（像素）
        """
        self._min_width = min_width
        self._min_height = min_height
        self._max_width = max_width
        self._max_height = max_height
        self._resize_margin = resize_margin
        self._resize_edge = self.EDGE_NONE
        self._is_resizing = False
        self._resize_start_pos = QPoint()
        self._resize_start_geometry = QRect()
        
        # 启用鼠标追踪以更新光标
        self.setMouseTracking(True)
    
    def _get_resize_edge(self, pos):
        """
        检测鼠标位置在哪个边缘
        
        Args:
            pos: 鼠标位置（窗口相对坐标）
            
        Returns:
            int: 边缘标识
        """
        rect = self.rect()
        margin = self._resize_margin
        edge = self.EDGE_NONE
        
        # 检测左右边缘
        if pos.x() <= margin:
            edge |= self.EDGE_LEFT
        elif pos.x() >= rect.width() - margin:
            edge |= self.EDGE_RIGHT
            
        # 检测上下边缘
        if pos.y() <= margin:
            edge |= self.EDGE_TOP
        elif pos.y() >= rect.height() - margin:
            edge |= self.EDGE_BOTTOM
            
        return edge
    
    def _update_cursor(self, edge):
        """
        根据边缘位置更新光标样式
        
        Args:
            edge: 边缘标识
        """
        cursor_map = {
            self.EDGE_LEFT: Qt.SizeHorCursor,
            self.EDGE_RIGHT: Qt.SizeHorCursor,
            self.EDGE_TOP: Qt.SizeVerCursor,
            self.EDGE_BOTTOM: Qt.SizeVerCursor,
            self.EDGE_TOPLEFT: Qt.SizeFDiagCursor,
            self.EDGE_TOPRIGHT: Qt.SizeBDiagCursor,
            self.EDGE_BOTTOMLEFT: Qt.SizeBDiagCursor,
            self.EDGE_BOTTOMRIGHT: Qt.SizeFDiagCursor,
        }
        
        if edge in cursor_map:
            self.setCursor(cursor_map[edge])
        else:
            self.unsetCursor()
    
    def mousePressEvent(self, event):
        """重写鼠标按下事件"""
        if event.button() == Qt.LeftButton and hasattr(self, '_resize_edge'):
            self._resize_edge = self._get_resize_edge(event.pos())
            
            if self._resize_edge != self.EDGE_NONE:
                self._is_resizing = True
                self._resize_start_pos = event.globalPosition().toPoint()
                self._resize_start_geometry = self.geometry()
                event.accept()
                return
        
        # 传递给其他处理器（例如 DraggableMixin）
        if hasattr(super(), 'mousePressEvent'):
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """重写鼠标移动事件"""
        if hasattr(self, '_is_resizing') and self._is_resizing:
            # 正在调整大小
            delta = event.globalPosition().toPoint() - self._resize_start_pos
            new_geo = QRect(self._resize_start_geometry)
            
            # 根据边缘调整几何形状
            if self._resize_edge & self.EDGE_LEFT:
                new_geo.setLeft(new_geo.left() + delta.x())
            if self._resize_edge & self.EDGE_RIGHT:
                new_geo.setRight(new_geo.right() + delta.x())
            if self._resize_edge & self.EDGE_TOP:
                new_geo.setTop(new_geo.top() + delta.y())
            if self._resize_edge & self.EDGE_BOTTOM:
                new_geo.setBottom(new_geo.bottom() + delta.y())
            
            # 应用尺寸限制
            if new_geo.width() < self._min_width:
                if self._resize_edge & self.EDGE_LEFT:
                    new_geo.setLeft(new_geo.right() - self._min_width)
                else:
                    new_geo.setWidth(self._min_width)
                    
            if new_geo.width() > self._max_width:
                if self._resize_edge & self.EDGE_LEFT:
                    new_geo.setLeft(new_geo.right() - self._max_width)
                else:
                    new_geo.setWidth(self._max_width)
                    
            if new_geo.height() < self._min_height:
                if self._resize_edge & self.EDGE_TOP:
                    new_geo.setTop(new_geo.bottom() - self._min_height)
                else:
                    new_geo.setHeight(self._min_height)
                    
            if new_geo.height() > self._max_height:
                if self._resize_edge & self.EDGE_TOP:
                    new_geo.setTop(new_geo.bottom() - self._max_height)
                else:
                    new_geo.setHeight(self._max_height)
            
            self.setGeometry(new_geo)
            event.accept()
            return
        
        # 更新光标（悬停检测）
        if hasattr(self, '_resize_edge') and not hasattr(self, '_is_dragging') or not self._is_dragging:
            edge = self._get_resize_edge(event.pos())
            self._update_cursor(edge)
        
        # 传递给其他处理器（例如 DraggableMixin）
        if hasattr(super(), 'mouseMoveEvent'):
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """重写鼠标释放事件"""
        if hasattr(self, '_is_resizing') and self._is_resizing:
            self._is_resizing = False
            self._resize_edge = self.EDGE_NONE
            event.accept()
        
        # 传递给其他处理器
        if hasattr(super(), 'mouseReleaseEvent'):
            super().mouseReleaseEvent(event)


class DraggableWindow(QWidget, DraggableMixin):
    """
    保留向后兼容的基类
    推荐使用 Mixin 方式：class MyWindow(QWidget, DraggableMixin, ResizableMixin)
    """
    def __init__(self, snap_to_top=True):
        super().__init__()
        self.setup_draggable(snap_to_top=snap_to_top)
