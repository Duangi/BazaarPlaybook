# gui/components/info_card.py
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel

class InfoCard(QFrame):
    """信息卡片组件 - 用于显示配置结果等信息"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("InfoCard")
        self._setup_ui()
        self._setup_style()
        
    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 15, 20, 15)
        self.layout.setSpacing(8)
        
        self.title_label = QLabel()
        self.title_label.setObjectName("InfoCardTitle")
        self.title_label.setWordWrap(True)
        
        self.content_label = QLabel()
        self.content_label.setObjectName("InfoCardContent")
        self.content_label.setWordWrap(True)
        
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.content_label)
        
    def _setup_style(self):
        self.setStyleSheet("""
            #InfoCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 204, 0, 0.08),
                    stop:1 rgba(255, 204, 0, 0.03));
                border: 1px solid rgba(255, 204, 0, 0.3);
                border-left: 4px solid #ffcc00;
                border-radius: 8px;
            }
            #InfoCardTitle {
                color: #ffcc00;
                font-size: 16px;
                font-weight: bold;
            }
            #InfoCardContent {
                color: #d0d0d0;
                font-size: 14px;
                line-height: 1.6;
            }
        """)
    
    def set_info(self, title: str, content: str):
        """设置卡片信息"""
        self.title_label.setText(title)
        self.content_label.setText(content)
