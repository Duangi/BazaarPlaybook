# gui/components/styled_button.py
from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

class StyledButton(QPushButton):
    """统一的可交互按钮组件，支持悬浮动画"""
    
    def __init__(self, text="", button_type="primary", parent=None):
        super().__init__(text, parent)
        self.button_type = button_type
        self._bg_color = QColor("#ffcc00")
        self.setCursor(Qt.PointingHandCursor)
        self._setup_style()
        
    def _setup_style(self):
        """根据按钮类型设置样式"""
        if self.button_type == "primary":
            self.setStyleSheet("""
                StyledButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #ffdb4d, stop:1 #ffcc00);
                    color: #1a1410;
                    border: none;
                    border-radius: 6px;
                    font-size: 16px;
                    font-weight: 700;
                    padding: 8px 18px;
                }
                StyledButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #ffe680, stop:1 #ffdb4d);
                }
                StyledButton:pressed {
                    background: #e6b800;
                    font-weight: 700;
                    padding: 8px 18px;
                }
                StyledButton:disabled {
                    background: #3d352f;
                    color: #666666;
                }
            """)
        elif self.button_type == "secondary":
            self.setStyleSheet("""
                StyledButton {
                    background: rgba(255, 204, 0, 0.15);
                    color: #ffcc00;
                    border: 2px solid #ffcc00;
                    border-radius: 6px;
                    font-size: 16px;
                    font-weight: 700;
                    padding: 8px 18px;
                }
                StyledButton:hover {
                    background: rgba(255, 204, 0, 0.25);
                    border-color: #ffdb4d;
                    color: #ffdb4d;
                }
                StyledButton:pressed {
                    background: rgba(255, 204, 0, 0.35);
                    font-weight: 700;
                    padding: 8px 18px;
                }
                StyledButton:disabled {
                    background: rgba(61, 53, 47, 0.3);
                    border-color: #3d352f;
                    color: #666666;
                }
            """)
        elif self.button_type == "close":
            self.setStyleSheet("""
                StyledButton {
                    background: transparent;
                    color: #888888;
                    border: none;
                    font-size: 20px;
                    font-weight: 700;
                }
                StyledButton:hover {
                    color: #ff4444;
                    background: rgba(255, 68, 68, 0.1);
                    border-radius: 4px;
                }
                StyledButton:pressed {
                    background: rgba(255, 68, 68, 0.2);
                    font-weight: 700;
                }
            """)

class GlowButton(StyledButton):
    """带发光效果的主要按钮"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, "primary", parent)
        self.setGraphicsEffect(None)  # 可以添加阴影效果
        
    def enterEvent(self, event):
        """鼠标悬浮时的发光效果"""
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """鼠标离开时移除发光"""
        super().leaveEvent(event)
