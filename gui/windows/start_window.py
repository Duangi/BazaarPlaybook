# gui/windows/start_window.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QFont
from gui.styles import START_WINDOW_STYLE
from gui.components.styled_button import StyledButton

class StartWindow(QWidget):
    entered = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.resize(700, 500) 
        self._drag_pos = QPoint()

        self._setup_ui()
        self.setStyleSheet(START_WINDOW_STYLE)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.container = QFrame()
        self.container.setObjectName("MainFrame")
        layout.addWidget(self.container)

        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(Qt.black)
        shadow.setOffset(0, 5)
        self.container.setGraphicsEffect(shadow)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(40, 30, 40, 40)
        container_layout.setSpacing(25)

        # 顶部关闭按钮
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.btn_close = StyledButton("✕", button_type="close")
        self.btn_close.setFixedSize(32, 32)
        self.btn_close.clicked.connect(self.close)
        top_bar.addWidget(self.btn_close)
        container_layout.addLayout(top_bar)

        # Logo 和标题区域
        title_section = QVBoxLayout()
        title_section.setSpacing(10)
        
        # 主标题
        title = QLabel("集市小抄")
        title.setObjectName("AppTitle")
        title.setAlignment(Qt.AlignCenter)
        title_section.addWidget(title)
        
        # 副标题
        subtitle = QLabel("BAZAAR ASSISTANT")
        subtitle.setObjectName("AppSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        title_section.addWidget(subtitle)
        
        container_layout.addLayout(title_section)
        
        # 版本信息卡片
        self.info_card = QFrame()
        self.info_card.setObjectName("InfoCard")
        info_layout = QVBoxLayout(self.info_card)
        info_layout.setContentsMargins(25, 20, 25, 20)
        info_layout.setSpacing(12)
        
        # 版本号
        version = QLabel("🎉 v2.1.0 - 核心引擎重构版")
        version.setObjectName("VersionText")
        info_layout.addWidget(version)
        
        # 分隔线
        divider = QFrame()
        divider.setObjectName("Divider")
        divider.setFixedHeight(1)
        info_layout.addWidget(divider)
        
        # 功能说明
        features = QLabel(
            "🧠 脑子是用来构筑的，数据交给小抄记<br>"
            "⚡ 智能识别 · 实时推荐 · 策略分析<br>"
            "🎮 助你在集市中运筹帷幄"
        )
        features.setObjectName("FeatureText")
        features.setWordWrap(True)
        info_layout.addWidget(features)
        
        # 免责声明
        disclaimer = QLabel("⚠️ 本工具由 B站@这是李Duang啊 免费发放，严禁买卖！")
        disclaimer.setObjectName("DisclaimerText")
        disclaimer.setWordWrap(True)
        info_layout.addWidget(disclaimer)
        
        container_layout.addWidget(self.info_card)
        
        container_layout.addStretch()

        # 底部进入按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.btn_enter = StyledButton("启动助手", button_type="primary")
        self.btn_enter.setFixedSize(220, 50)
        self.btn_enter.clicked.connect(self._on_enter)
        
        button_layout.addWidget(self.btn_enter)
        button_layout.addStretch()
        container_layout.addLayout(button_layout)

    def _on_enter(self):
        self.entered.emit()
        self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
