"""
设置页面 (Settings Page)
包含 UI 缩放、语言切换、自动收起等设置
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QScrollArea,
                               QCheckBox, QSpinBox, QButtonGroup, QRadioButton)
from PySide6.QtCore import Qt, Signal, QSettings
from PySide6.QtGui import QFont


class SettingsPage(QWidget):
    """
    设置页面
    功能：
    1. UI 全局缩放滑块
    2. 语言切换（简中/繁中/英文）
    3. 自动收起设置（开关 + 延迟时间）
    """
    
    # 信号定义
    scale_changed = Signal(float)  # UI 缩放改变
    language_changed = Signal(str)  # 语言改变 (zh_CN / zh_TW / en_US)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # ✅ 使用与主窗口相同的设置存储（统一使用 SidebarWindow）
        self.settings = QSettings("Reborn", "SidebarWindow")
        
        self._init_ui()
        self._load_settings()
    
    def _init_ui(self):
        """初始化 UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(30)
        
        # 标题
        title = QLabel("⚙️ 系统设置")
        title.setObjectName("PageTitle")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        content_layout.addWidget(title)
        
        # === 1. UI 缩放设置 ===
        scale_group = self._create_scale_section()
        content_layout.addWidget(scale_group)
        
        # === 2. 语言设置 ===
        lang_group = self._create_language_section()
        content_layout.addWidget(lang_group)
        
        # 弹性空间
        content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
    
    def _create_scale_section(self) -> QWidget:
        """创建 UI 缩放设置区域"""
        group = QFrame()
        group.setObjectName("SettingGroup")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        header = QLabel("🎨 界面缩放")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)
        
        # 说明
        desc = QLabel("调整整个应用的界面大小（包括所有组件）")
        desc.setObjectName("SettingDesc")
        layout.addWidget(desc)
        
        # ✅ 改用加减号控制 + 数值显示
        control_layout = QHBoxLayout()
        
        # 减号按钮
        self.decrease_btn = QPushButton("−")
        self.decrease_btn.setObjectName("ScaleButton")
        self.decrease_btn.setFixedSize(50, 40)
        self.decrease_btn.setCursor(Qt.PointingHandCursor)
        self.decrease_btn.clicked.connect(self._on_decrease_scale)
        control_layout.addWidget(self.decrease_btn)
        
        # 当前缩放值显示
        self.scale_value = 100  # 存储当前值（百分比）
        self.scale_label = QLabel("100%")
        self.scale_label.setObjectName("ScaleValue")
        self.scale_label.setFixedWidth(120)
        self.scale_label.setAlignment(Qt.AlignCenter)
        scale_label_font = QFont()
        scale_label_font.setPointSize(16)
        scale_label_font.setBold(True)
        self.scale_label.setFont(scale_label_font)
        control_layout.addWidget(self.scale_label)
        
        # 加号按钮
        self.increase_btn = QPushButton("+")
        self.increase_btn.setObjectName("ScaleButton")
        self.increase_btn.setFixedSize(50, 40)
        self.increase_btn.setCursor(Qt.PointingHandCursor)
        self.increase_btn.clicked.connect(self._on_increase_scale)
        control_layout.addWidget(self.increase_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # 预设按钮
        preset_layout = QHBoxLayout()
        preset_label = QLabel("快速预设：")
        preset_layout.addWidget(preset_label)
        
        for percentage, label in [(75, "小"), (100, "标准"), (125, "大"), (150, "超大")]:
            btn = QPushButton(label)
            btn.setObjectName("PresetButton")
            btn.setFixedWidth(60)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, p=percentage: self._set_scale_value(p))
            preset_layout.addWidget(btn)
        
        preset_layout.addStretch()
        layout.addLayout(preset_layout)
        
        return group
    
    def _create_language_section(self) -> QWidget:
        """创建语言设置区域"""
        group = QFrame()
        group.setObjectName("SettingGroup")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        header = QLabel("🌐 语言 / Language")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)
        
        # 说明
        desc = QLabel("选择界面语言（实时生效）")
        desc.setObjectName("SettingDesc")
        layout.addWidget(desc)
        
        # 语言选项（单选按钮组）
        lang_layout = QHBoxLayout()
        lang_layout.setSpacing(20)
        
        self.lang_group = QButtonGroup(self)
        
        langs = [
            ("zh_CN", "简体中文", "🇨🇳"),
            ("zh_TW", "繁體中文", "🇭🇰"),
            ("en_US", "English", "🇺🇸")
        ]
        
        for lang_code, lang_name, flag in langs:
            radio = QRadioButton(f"{flag} {lang_name}")
            radio.setObjectName("LanguageRadio")
            radio.setCursor(Qt.PointingHandCursor)
            radio.setProperty("lang_code", lang_code)
            self.lang_group.addButton(radio)
            lang_layout.addWidget(radio)
            
            # 默认选中简中
            if lang_code == "zh_CN":
                radio.setChecked(True)
        
        lang_layout.addStretch()
        layout.addLayout(lang_layout)
        
        # 绑定信号
        self.lang_group.buttonClicked.connect(self._on_language_changed)
        
        return group
    
    def _on_decrease_scale(self):
        """减小缩放比例（每次5%）"""
        new_value = max(50, self.scale_value - 5)  # 最小50%
        self._set_scale_value(new_value)
    
    def _on_increase_scale(self):
        """增大缩放比例（每次5%）"""
        new_value = min(200, self.scale_value + 5)  # 最大200%
        self._set_scale_value(new_value)
    
    def _set_scale_value(self, value):
        """设置缩放值"""
        self.scale_value = value
        scale = value / 100.0
        self.scale_label.setText(f"{value}%")
        
        # 保存设置
        self.settings.setValue("ui_scale", scale)
        
        # 发送信号
        self.scale_changed.emit(scale)
    
    def _on_language_changed(self, button):
        """语言切换"""
        lang_code = button.property("lang_code")
        
        # 保存设置
        self.settings.setValue("language", lang_code)
        
        # 发送信号
        self.language_changed.emit(lang_code)
        
        print(f"[Settings] Language changed to: {lang_code}")
    
    def _load_settings(self):
        """加载保存的设置"""
        # 加载 UI 缩放
        scale = self.settings.value("ui_scale", 1.0, type=float)
        self.scale_value = int(scale * 100)
        self.scale_label.setText(f"{self.scale_value}%")
        
        # 加载语言
        lang = self.settings.value("language", "zh_CN", type=str)
        for button in self.lang_group.buttons():
            if button.property("lang_code") == lang:
                button.setChecked(True)
                break
    
    def get_current_scale(self) -> float:
        """获取当前缩放值"""
        return self.scale_value / 100.0
    
    def get_current_language(self) -> str:
        """获取当前语言"""
        for button in self.lang_group.buttons():
            if button.isChecked():
                return button.property("lang_code")
        return "zh_CN"
    
    def update_scale(self, scale: float):
        """更新页面缩放（外部调用）"""
        # 这里可以添加页面内组件的缩放逻辑
        # 目前由于使用了样式表的动态缩放，无需额外处理
        pass
