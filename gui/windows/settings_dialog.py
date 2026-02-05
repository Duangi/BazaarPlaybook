# gui/windows/settings_dialog.py
"""设置对话框"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QSlider, QFrame, QPushButton)
from PySide6.QtCore import Qt, Signal
from gui.components.styled_button import StyledButton

class SettingsDialog(QDialog):
    """设置对话框"""
    
    scale_changed = Signal(float)  # 缩放比例改变信号
    
    def __init__(self, current_scale=1.0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 300)
        self._current_scale = current_scale
        self._setup_ui()
        self._setup_style()
        
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 主容器
        container = QFrame()
        container.setObjectName("SettingsContainer")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(20)
        
        # 标题栏
        header_layout = QHBoxLayout()
        title = QLabel("⚙️ 设置")
        title.setObjectName("SettingsTitle")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        close_btn = StyledButton("✕", button_type="close")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        main_layout.addLayout(header_layout)
        
        # 分隔线
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background: rgba(255, 204, 0, 0.2); max-height: 1px;")
        main_layout.addWidget(divider)
        
        # 缩放设置
        scale_label = QLabel("界面缩放")
        scale_label.setObjectName("SettingLabel")
        main_layout.addWidget(scale_label)
        
        # 缩放滑块
        slider_layout = QHBoxLayout()
        
        # 小号标签
        small_label = QLabel("小")
        small_label.setStyleSheet("color: #888; font-size: 12px;")
        slider_layout.addWidget(small_label)
        
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setMinimum(50)  # 0.5倍
        self.scale_slider.setMaximum(200)  # 2.0倍
        self.scale_slider.setValue(int(self._current_scale * 100))
        self.scale_slider.setTickPosition(QSlider.TicksBelow)
        self.scale_slider.setTickInterval(25)
        self.scale_slider.valueChanged.connect(self._on_scale_changed)
        slider_layout.addWidget(self.scale_slider, 1)
        
        # 大号标签
        large_label = QLabel("大")
        large_label.setStyleSheet("color: #888; font-size: 12px;")
        slider_layout.addWidget(large_label)
        
        main_layout.addLayout(slider_layout)
        
        # 当前值显示
        value_layout = QHBoxLayout()
        value_layout.addStretch()
        
        self.value_label = QLabel(f"{self._current_scale:.1f}x")
        self.value_label.setObjectName("ScaleValue")
        value_layout.addWidget(self.value_label)
        
        # 重置按钮
        reset_btn = StyledButton("重置", button_type="secondary")
        reset_btn.setFixedSize(60, 28)
        reset_btn.clicked.connect(self._reset_scale)
        value_layout.addWidget(reset_btn)
        
        value_layout.addStretch()
        main_layout.addLayout(value_layout)
        
        # 提示文字
        hint = QLabel("💡 调整界面大小以适应不同分辨率屏幕")
        hint.setObjectName("SettingHint")
        hint.setWordWrap(True)
        main_layout.addWidget(hint)
        
        main_layout.addStretch()
        
        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        apply_btn = StyledButton("应用", button_type="primary")
        apply_btn.setFixedSize(100, 36)
        apply_btn.clicked.connect(self.accept)
        button_layout.addWidget(apply_btn)
        
        cancel_btn = StyledButton("取消", button_type="secondary")
        cancel_btn.setFixedSize(100, 36)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(button_layout)
        
        layout.addWidget(container)
        
    def _setup_style(self):
        """设置样式"""
        self.setStyleSheet(f"""
            #SettingsContainer {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #241f1c, stop:1 #1a1410);
                border: 2px solid #ffcc00;
                border-radius: 12px;
            }}
            #SettingsTitle {{
                color: #ffcc00;
                font-size: 20px;
                font-weight: bold;
            }}
            #SettingLabel {{
                color: #f0f0f0;
                font-size: 15px;
                font-weight: bold;
                margin-top: 10px;
            }}
            #ScaleValue {{
                color: #ffcc00;
                font-size: 18px;
                font-weight: bold;
            }}
            #SettingHint {{
                color: #888888;
                font-size: 12px;
                background: rgba(255, 204, 0, 0.05);
                padding: 8px;
                border-radius: 6px;
            }}
            QSlider::groove:horizontal {{
                background: rgba(255, 204, 0, 0.1);
                height: 8px;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ffdb4d, stop:1 #ffcc00);
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background: #ffdb4d;
            }}
            QSlider::sub-page:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ffcc00, stop:1 #d4af37);
                border-radius: 4px;
            }}
        """)
        
    def _on_scale_changed(self, value):
        """滑块值改变"""
        scale = value / 100.0
        self._current_scale = scale
        self.value_label.setText(f"{scale:.1f}x")
        
    def _reset_scale(self):
        """重置缩放"""
        self.scale_slider.setValue(100)
        
    def get_scale(self):
        """获取当前缩放值"""
        return self._current_scale
        
    def mousePressEvent(self, event):
        """允许拖动对话框"""
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.pos()
            
    def mouseMoveEvent(self, event):
        """拖动对话框"""
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
