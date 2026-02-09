"""
设置页面 (Settings Page)
包含 UI 缩放、语言切换、自动收起等设置
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QScrollArea,
                               QCheckBox, QSpinBox, QButtonGroup, QRadioButton)
from PySide6.QtCore import Qt, Signal, QSettings
from PySide6.QtGui import QFont, QColor
from loguru import logger

from utils.logger import setup_logger
from data_manager.config_manager import ConfigManager

class SettingsPage(QWidget):
    """
    设置页面
    功能：
    1. UI 全局缩放滑块
    2. 语言切换（简中/繁中/英文）
    3. 自动收起设置（开关 + 延迟时间）
    4. 自动扫描设置 (YOLO + Overlay)
    """
    
    # 信号定义
    scale_changed = Signal(float)  # UI 缩放改变
    language_changed = Signal(str)  # 语言改变 (zh_CN / zh_TW / en_US)
    reset_overlay_pos_requested = Signal() # 请求重置悬浮窗位置
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # ✅ 使用与主窗口相同的设置存储（统一使用 SidebarWindow）
        self.settings = QSettings("Reborn", "SidebarWindow")
        # 配置文件管理器
        self.config_manager = ConfigManager()
        
        self._init_ui()
        self._load_settings()
    
    def _init_ui(self):
        """初始化 UI"""
        # Apply Global Styles specific to Settings Page
        self.setStyleSheet("""
            QWidget {
                color: #f0f0f0;
                font-family: 'Microsoft YaHei', sans-serif;
            }
            QFrame#SettingGroup {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
            }
            QLabel#PageTitle {
                color: #f59e0b;
                margin-bottom: 10px;
            }
            QLabel#SettingDesc {
                color: #888;
                font-size: 10pt;
            }
            QPushButton {
                background-color: rgba(60, 60, 65, 0.8);
                border: 1px solid #555;
                border-radius: 4px;
                color: #fff;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: rgba(80, 80, 85, 0.9);
                border-color: #f59e0b;
            }
            QPushButton:checked {
                background-color: #f59e0b;
                color: #000;
            }
            QPushButton#ScaleButton {
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton#PresetButton {
                font-size: 12px;
            }
            QCheckBox {
                spacing: 8px;
                color: #eee;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #666;
                border-radius: 4px;
                background: #222;
            }
            QCheckBox::indicator:checked {
                background-color: #f59e0b;
                border-color: #f59e0b;
                /* image: url(assets/icon/check.svg); removed */
            }
            QSpinBox {
                background-color: #222;
                border: 1px solid #555;
                border-radius: 4px;
                color: #fff;
                padding: 4px;
                min-width: 60px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 16px; 
                background: #333;
            }
            QRadioButton {
                color: #eee;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #666;
                border-radius: 9px;
                background: #222;
            }
            QRadioButton::indicator:checked {
                background-color: #f59e0b;
                border: 3px solid #000;
            }
        """)

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

        # === 1.5 交互设置 ===
        interaction_group = self._create_interaction_section()
        content_layout.addWidget(interaction_group)
        
        # === 2. 语言设置 ===
        lang_group = self._create_language_section()
        content_layout.addWidget(lang_group)

        # === 3. 自动扫描设置 ===
        scan_group = self._create_autoscan_section()
        content_layout.addWidget(scan_group)

        # === 4. 开发者选项 ===
        dev_group = self._create_developer_section()
        content_layout.addWidget(dev_group)
        
        # 弹性空间
        content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def _create_developer_section(self) -> QWidget:
        """创建开发者选项区域"""
        group = QFrame()
        group.setObjectName("SettingGroup")
        group.setStyleSheet("""
            QFrame#SettingGroup {
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            QLabel { color: #ddd; }
            QCheckBox { 
                color: #ddd; 
                spacing: 8px;
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #888;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #f59e0b;
                border-color: #f59e0b;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        header = QLabel("🛠️ 开发者选项")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)
        
        # 调试模式开关
        self.chk_debug = QCheckBox("开启调试模式 (Debug Mode)")
        self.chk_debug.setChecked(self.config_manager.settings.get("debug_mode", False))
        self.chk_debug.toggled.connect(self._on_debug_toggled)
        layout.addWidget(self.chk_debug)
        
        desc = QLabel("开启后，控制台将输出详细的运行日志（仅建议开发者使用）")
        desc.setStyleSheet("color: #888; font-size: 12px; font-style: italic;")
        layout.addWidget(desc)
        
        return group

    def _on_debug_toggled(self, checked: bool):
        """调试模式切换"""
        self.config_manager.save({"debug_mode": checked})
        # 立即应用日志设置
        setup_logger(is_gui_app=True, debug_mode=checked)

    def _create_interaction_section(self) -> QWidget:
        """创建交互设置区域"""
        group = QFrame()
        group.setObjectName("SettingGroup")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        header = QLabel("🖱️ 交互设置 / Interaction")
        header_font = QFont(); header_font.setPointSize(14); header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)
        
        # A. Delay
        delay_layout = QHBoxLayout()
        delay_label = QLabel("悬浮显示延迟 (ms):")
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(0, 5000)
        self.delay_spin.setSingleStep(100)
        curr_delay = self.config_manager.settings.get("hover_delay", 200)
        self.delay_spin.setValue(int(curr_delay))
        self.delay_spin.valueChanged.connect(self._on_delay_changed)
        
        delay_layout.addWidget(delay_label)
        delay_layout.addWidget(self.delay_spin)
        delay_layout.addStretch()
        layout.addLayout(delay_layout)
        
        # B. Hotkey
        hotkey_layout = QHBoxLayout()
        hotkey_label = QLabel("详情唤起热键:")
        current_hotkey = self.config_manager.settings.get("detail_hotkey", "")
        self.hotkey_btn = QPushButton(current_hotkey if current_hotkey else "点击设置...")
        self.hotkey_btn.setCheckable(True)
        self.hotkey_btn.clicked.connect(self._on_hotkey_btn_clicked)
        self.hotkey_btn.setFixedWidth(150)
        self.hotkey_btn.setCursor(Qt.PointingHandCursor)
        
        hotkey_layout.addWidget(hotkey_label)
        hotkey_layout.addWidget(self.hotkey_btn)
        hotkey_layout.addStretch()
        layout.addLayout(hotkey_layout)
        
        # Tips
        tip = QLabel("提示: 设置热键后，即使关闭悬浮显示，在游戏内对准物品按住热键即可查看详情。按键唤起的窗口将保持常驻。")
        tip.setStyleSheet("color: #888; font-size: 9pt;")
        tip.setWordWrap(True)
        layout.addWidget(tip)

        return group

    def _on_delay_changed(self, value):
        self.config_manager.save({"hover_delay": value})


    def _on_hotkey_btn_clicked(self, checked):
        if checked:
            # Open Recorder Dialog
            from gui.widgets.hotkey_recorder_dialog import HotkeyRecorderDialog
            dlg = HotkeyRecorderDialog(self.window()) # Parent to main window for modal
            dlg.hotkey_recorded.connect(self._on_hotkey_recorded)
            # uncheck first, let dialog handle logic
            self.hotkey_btn.setChecked(False)
            dlg.exec_()
        else:
             pass

    def _on_hotkey_recorded(self, key_str):
        logger.info(f"Hotkey set to: {key_str}")
        self.config_manager.save({"detail_hotkey": key_str})
        self._update_hotkey_text()

    def keyPressEvent(self, event):
        super().keyPressEvent(event)

    def _update_hotkey_text(self):
         current = self.config_manager.settings.get("detail_hotkey", "")
         self.hotkey_btn.setText(current if current else "点击设置...")
        
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
    
    def _create_autoscan_section(self) -> QWidget:
        """创建自动扫描设置区域"""
        group = QFrame()
        group.setObjectName("SettingGroup")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        header = QLabel("🤖 自动助手 / Auto Assist")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)

        # 1. 自动扫描开关
        self.chk_auto_scan = QCheckBox("启用 YOLO 自动扫描 (Enable Auto Scan)")
        self.chk_auto_scan.setCursor(Qt.PointingHandCursor)
        self.chk_auto_scan.setChecked(self.config_manager.settings.get("auto_scan_enabled", False))
        self.chk_auto_scan.toggled.connect(lambda c: self.config_manager.save({"auto_scan_enabled": c}))
        layout.addWidget(self.chk_auto_scan)

        # 2. 悬浮窗开关
        self.chk_overlay = QCheckBox("悬浮显示详情 (Floating Detail Overlay)")
        self.chk_overlay.setCursor(Qt.PointingHandCursor)
        self.chk_overlay.setChecked(self.config_manager.settings.get("overlay_enabled", False))
        self.chk_overlay.toggled.connect(lambda c: self.config_manager.save({"overlay_enabled": c}))
        layout.addWidget(self.chk_overlay)

        # 3. 重置位置按钮
        btn_reset = QPushButton("重置详情框位置 (Reset Overlay Position)")
        btn_reset.setCursor(Qt.PointingHandCursor)
        btn_reset.setFixedWidth(250)
        btn_reset.clicked.connect(self.reset_overlay_pos_requested.emit)
        layout.addWidget(btn_reset)

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
