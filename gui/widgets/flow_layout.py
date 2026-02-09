"""
流式布局 - 支持自动换行
"""
from PySide6.QtWidgets import QLayout, QLayoutItem, QSizePolicy
from PySide6.QtCore import Qt, QRect, QSize, QPoint


class FlowLayout(QLayout):
    """
    流式布局 - 当一行放不下时自动换行
    参考Qt官方示例实现
    """
    
    def __init__(self, parent=None, margin=0, h_spacing=-1, v_spacing=-1):
        super().__init__(parent)
        
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        
        self._h_space = h_spacing
        self._v_space = v_spacing
        self._item_list = []
    
    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)
    
    def addItem(self, item: QLayoutItem):
        self._item_list.append(item)
    
    def horizontalSpacing(self):
        if self._h_space >= 0:
            return self._h_space
        else:
            return self._smart_spacing(Qt.Horizontal)
    
    def verticalSpacing(self):
        if self._v_space >= 0:
            return self._v_space
        else:
            return self._smart_spacing(Qt.Vertical)
    
    def count(self):
        return len(self._item_list)
    
    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None
    
    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None
    
    def expandingDirections(self):
        return Qt.Orientation(0)
    
    def hasHeightForWidth(self):
        return True
    
    def heightForWidth(self, width):
        height = self._do_layout(QRect(0, 0, width, 0), True)
        return height
    
    def setGeometry(self, rect: QRect):
        super().setGeometry(rect)
        self._do_layout(rect, False)
    
    def sizeHint(self):
        return self.minimumSize()
    
    def minimumSize(self):
        size = QSize()
        
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size
    
    def _do_layout(self, rect: QRect, test_only: bool):
        left, top, right, bottom = self.getContentsMargins()
        effective_rect = rect.adjusted(+left, +top, -right, -bottom)
        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0
        
        for item in self._item_list:
            wid = item.widget()
            space_x = self.horizontalSpacing()
            if space_x == -1:
                space_x = wid.style().layoutSpacing(
                    QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal
                )
            space_y = self.verticalSpacing()
            if space_y == -1:
                space_y = wid.style().layoutSpacing(
                    QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical
                )
            
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > effective_rect.right() and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0
            
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            
            x = next_x
            line_height = max(line_height, item.sizeHint().height())
        
        return y + line_height - rect.y() + bottom
    
    def _smart_spacing(self, pm):
        parent = self.parent()
        if not parent:
            return -1
        
        if parent.isWidgetType():
            return parent.style().pixelMetric(pm, None, parent)
        else:
            return parent.spacing()
