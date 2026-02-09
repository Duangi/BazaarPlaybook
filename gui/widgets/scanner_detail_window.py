"""
Scanner Detail Window (独立扫描结果卡片窗口)
- 样式引用 ItemDetailCard
- 高度自适应
- 可拖动
- 右下角缩放手柄 (调整 content_scale)
- 独立记住位置和缩放比例
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame, QLabel, QSizeGrip
from PySide6.QtCore import Qt, QSettings, Signal, QSize, QPoint, QRect
from PySide6.QtGui import QCursor, QMouseEvent

from gui.widgets.item_detail_card import ItemDetailCard
from gui.utils.frameless_helper import FramelessHelper
from gui.styles import COLOR_GOLD

class ScannerDetailWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("Reborn", "ScannerDetailWindow")
        
        # 1. Load Settings
        self.content_scale = self.settings.value("scale", 1.0, type=float)
        self.content_scale = max(0.6, min(2.5, self.content_scale)) # Limit scale
        
        self.is_sticky = False # New flag: if True, do not hide automatically
        
        # 2. Window Setup
        # Use Popup or Tool. Popup implicitly closes on outside click but can be tricky with inputs.
        # We try manual approach first with activation.
        self.setWindowFlags(
            Qt.WindowType.Tool | 
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        # self.setAttribute(Qt.WA_ShowWithoutActivating) # Allow activation for focus logic
        
        # 3. UI Init
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Container for style
        self.container = QFrame()
        self.container.setObjectName("ScannerCardContainer")
        self.container.setStyleSheet(f"""
            #ScannerCardContainer {{
                background-color: rgba(15, 15, 20, 0.95);
                border: 1px solid {COLOR_GOLD};
                border-radius: 10px;
            }}
        """)
        self.main_layout.addWidget(self.container)
        
        # Content Layout
        self.content_layout = QVBoxLayout(self.container)
        # Margin adapts to scale
        m = int(10 * self.content_scale)
        self.content_layout.setContentsMargins(m, m, m, m)
        self.content_layout.setSpacing(0)
        
        # 4. Scale Handle (Bottom Right)
        self.scale_handle = QLabel(self.container)
        self.scale_handle.setCursor(Qt.SizeFDiagCursor)
        self.scale_handle.setFixedSize(16, 16)
        self.scale_handle.setStyleSheet(f"""
            background-color: {COLOR_GOLD};
            border-radius: 8px;
            border: 2px solid #fff;
        """)
        # Corner position is managed in resizeEvent
        self.scale_handle.raise_()
        
        # Handle state
        self._resizing = False
        self._resize_start_pos = None
        self._resize_start_scale = 1.0
        
        self.scale_handle.mousePressEvent = self._handle_press
        self.scale_handle.mouseMoveEvent = self._handle_move
        self.scale_handle.mouseReleaseEvent = self._handle_release
        
        # 5. Helper for dragging position (but NOT resizing via edges, to keep height adaptive logic simple)
        self.frameless = FramelessHelper(self, enable_drag=True, enable_resize=False)

        # 6. Restore Position
        pos = self.settings.value("pos")
        if pos and isinstance(pos, QPoint):
            self.move(pos)
        else:
            # Default center? or somewhere safe
            self.resize(300, 400) 

        self.current_item_id = None
        self.card_widget = None


    def focusOutEvent(self, event):
        """Close if sticky and focus lost"""
        if self.is_sticky:
            # When active, clicking outside sends FocusOut
            # But ensure we don't hide if clicking inside (which shouldn't trigger FocusOut for the window usually, but check children)
            pass 
        
        # Logic: If focus lost to another app/window, hide
        if not self.isActiveWindow():
             # Safety: Check if we are really resizing
             if not getattr(self, '_resizing', False):
                 self.hide()
                 self.is_sticky = False
                 
        super().focusOutEvent(event)

    def changeEvent(self, event):
        # Activation Change is more reliable than FocusOut for top-level windows
        if event.type() == event.Type.ActivationChange:
            if not self.isActiveWindow() and self.isVisible():
                 if not getattr(self, '_resizing', False):
                     self.hide()
                     self.is_sticky = False
        super().changeEvent(event)

    def keyPressEvent(self, event):
        """Allow closing with ESC"""
        from PySide6.QtCore import Qt
        if event.key() == Qt.Key_Escape:
            self.hide()
            self.is_sticky = False
        super().keyPressEvent(event)

    def show_item(self, item_id, sticky=False):
        """显示物品详情"""
        # sticky: persistent window until click outside
        if sticky:
            self.is_sticky = True
            # Activate window to capture focus (so focusOut works)
            self.setAttribute(Qt.WA_ShowWithoutActivating, False)
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            # We need to re-show if flags change
        else:
            self.is_sticky = False
            self.setAttribute(Qt.WA_ShowWithoutActivating, True)

            
        # If same item, just show
        if item_id == self.current_item_id and self.isVisible():
            self.raise_()
            return

        self.current_item_id = item_id
        
        # Clear existing
        self._clear_content()
        
        # Create Card
        # Note: default_expanded=True to show details immediately
        self.card_widget = ItemDetailCard(
            item_id=item_id, 
            item_type="card", # Assuming generic card/item
            default_expanded=True,
            enable_tier_click=True,
            content_scale=self.content_scale
        )
        # Make card background transparent to blend with container
        self.card_widget.setStyleSheet("background: transparent;")
        
        self.content_layout.addWidget(self.card_widget)
        
        # Resize to fit content
        self.container.adjustSize()
        self.adjustSize()
        
        # Show
        self.show()
        self.raise_()
        if sticky:
            self.activateWindow() # Grab focus immediately so clicking away triggers ActivationChange
        # If ItemDetailCard changes size (e.g. tier switch), we need to adjust window size
        # However, ItemDetailCard layout usually updates automatically.
        # We just need to resize THIS window to fit hint.
        
        self.content_layout.addWidget(self.card_widget)
        
        # Force layout update and resize
        self.card_widget.adjustSize()
        self.adjust_size_to_content()
        
        self.show()
        self.raise_()
        
        if sticky:
            self.activateWindow()
            self.setFocus()
        
    def _clear_content(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.card_widget = None

    def adjust_size_to_content(self):
        """根据内容调整窗口大小"""
        # Process events to let layout calculate
        # self.container.adjustSize()
        # self.adjustSize() 
        # Sometimes adjustSize() needs help with layout constraints
        
        # Calculate expected width based on scale?
        # ItemDetailCard usually fits width. 
        # Let's set a fixed width based on scale and let height adapt
        base_width = 300 # Base width for card
        target_width = int(base_width * self.content_scale)
        
        # Apply standard width constraint to container or card?
        # ItemDetailCard usually expands to fill.
        
        # We resize the window width, layout makes card fill it, card determines height.
        self.setFixedWidth(target_width)
        
        # Now height
        # Yield to let layout update
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
        
        content_height = self.container.sizeHint().height()
        self.setFixedHeight(content_height)
        
        # Update handle pos
        self._update_handle_pos()

    def resizeEvent(self, event):
        self._update_handle_pos()
        super().resizeEvent(event)

    def _update_handle_pos(self):
        """Keep resize handle at bottom right"""
        s = self.scale_handle.size()
        m = 10 # Offset
        self.scale_handle.move(self.width() - s.width() - 5, self.height() - s.height() - 5)

    def closeEvent(self, event):
        self.settings.setValue("pos", self.pos())
        self.settings.setValue("scale", self.content_scale)
        super().closeEvent(event)
        
    def mouseReleaseEvent(self, event):
        """Save pos on drag end"""
        super().mouseReleaseEvent(event)
        self.settings.setValue("pos", self.pos())

    # --- Scale Handle Logic ---
    def _handle_press(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._resizing = True
            self._resize_start_pos = event.globalPosition().toPoint()
            self._resize_start_scale = self.content_scale
            event.accept()

    def _handle_move(self, event: QMouseEvent):
        if self._resizing:
            delta = event.globalPosition().toPoint() - self._resize_start_pos
            # Dragging right/down increases scale
            diff = (delta.x() + delta.y()) / 200.0 # Sensitivity
            
            new_scale = self._resize_start_scale + diff
            new_scale = max(0.6, min(2.5, new_scale))
            
            if new_scale != self.content_scale:
                self.content_scale = new_scale
                self._apply_scale()
            
            event.accept()

    def _handle_release(self, event: QMouseEvent):
        self._resizing = False
        self.settings.setValue("scale", self.content_scale)

    def _apply_scale(self):
        """Apply new scale to content"""
        # Update styling
        m = int(10 * self.content_scale)
        self.content_layout.setContentsMargins(m, m, m, m)
        
        # Re-create card or update if supported? 
        # ItemDetailCard doesn't support dynamic scale update easily without recreation 
        # or we update its property and reload?
        # Re-creation is safer to apply all fonts/sizes
        if self.current_item_id:
             self.show_item(self.current_item_id)
        else:
             self.adjust_size_to_content()

