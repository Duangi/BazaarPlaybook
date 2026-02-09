import sys
import os
import json
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QStackedWidget, QButtonGroup)
from PySide6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, Signal, QSize, QSettings, QRect, QTimer
from PySide6.QtGui import QIcon
import gui.styles as styles
from gui.utils.frameless_helper import FramelessHelper
from utils.icon_helper import create_colored_svg_icon
from gui.pages.monster_overview_page import MonsterOverviewPage
from gui.pages.settings_page import SettingsPage
from gui.pages.history_page import HistoryPage
from gui.pages.encyclopedia_page import EncyclopediaPage
from utils.i18n import get_i18n
from loguru import logger

class SidebarWindow(QWidget):
    collapse_to_island = Signal()  # 收起到灵动岛信号
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # ✅ 窗口位置配置文件路径
        self.config_file = os.path.join("user_data", "sidebar_window.json")
        os.makedirs("user_data", exist_ok=True)
        
        # ✅ 收起状态标记
        self.is_auto_collapsed = False  # 是否处于收起状态
        
        # ✅ 鼠标离开延迟定时器（用于自动收起）
        self.leave_timer = QTimer()
        self.leave_timer.setSingleShot(True)
        self.leave_timer.timeout.connect(self._check_auto_collapse)
        self.leave_delay = 500  # 500ms延迟
        
        # ✅ 保存位置的防抖定时器
        self.save_timer = QTimer()
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(300)  # 300ms 防抖
        self.save_timer.timeout.connect(self._save_window_geometry_now)

        # 防抖/频率限制辅助
        self._save_pending = False
        self._last_saved_time = 0.0
        self._min_save_interval = 2.0  # seconds, 不要在短时间内频繁写磁盘
        
        # ✅ 防止缩放时抖动
        self._is_scaling = False
        
        # 设置窗口尺寸限制（必须在创建 FramelessHelper 之前设置）
        self.setMinimumSize(400, 500)
        self.setMaximumSize(800, 1200)
        
        # ✅ 启用完整的拖拽和8方向调整大小功能
        # 增加边缘检测范围，避免与滚动条冲突
        self.frameless_helper = FramelessHelper(
            self, 
            margin=8,           # 边缘检测区域调整为8px
            snap_to_top=True,   # 启用顶部吸附
            enable_drag=True,   # 启用拖拽
            enable_resize=True, # ✅ 启用8方向调整大小
            debug=False         # 关闭调试输出
        )
        
        self.current_scale = 1.0
        self.nav_buttons = []  # 存储所有导航按钮
        self.i18n = get_i18n()  # 本地化管理器
        self._init_base_structure()
        self._init_nav_content()  # 初始化导航栏内容
        self._init_pages()  # 初始化页面内容
        self._init_animations()  # 初始化动画
        self.update_ui_scale(1.0)
        
        # ✅ 加载保存的窗口位置和大小
        self._load_window_geometry()

    def _init_base_structure(self):
        # 1. 根布局
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0) # 阴影边距

        # 2. 主容器
        self.main_container = QFrame()
        self.main_container.setObjectName("SidebarMain")
        # ✅ 启用鼠标追踪，让边缘能检测鼠标
        self.main_container.setMouseTracking(True)
        self.root_layout.addWidget(self.main_container)

        # 3. 主容器内部纵向布局
        self.v_layout = QVBoxLayout(self.main_container)
        self.v_layout.setContentsMargins(0, 0, 0, 0)
        self.v_layout.setSpacing(0)

        # A. 顶部标题栏
        self.title_bar = QFrame()
        self.title_bar.setObjectName("TitleBar")
        self.title_bar.setAttribute(Qt.WA_StyledBackground, True)
        self.v_layout.addWidget(self.title_bar)
        
        # 标题栏布局
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(20, 0, 20, 0)
        
        # 标题文字
        title_label = QLabel("集市小抄")
        title_label.setObjectName("AppTitle")
        title_layout.addWidget(title_label)
        
        # ✅ 删除收起按钮，改为自动收起
        title_layout.addStretch(1)  # 占据剩余空间
        
        # 语言切换按钮（可选）
        self.lang_btn = QPushButton("🌐 简中")
        self.lang_btn.setObjectName("LangButton")
        self.lang_btn.setCursor(Qt.PointingHandCursor)
        self.lang_btn.setFixedSize(70, 30)
        self.lang_btn.clicked.connect(self._on_lang_clicked)
        title_layout.addWidget(self.lang_btn)

        # B. 工作区 (作为 NavRail 的父级)
        self.workspace = QFrame()
        self.workspace.setObjectName("Workspace")
        self.workspace.setAttribute(Qt.WA_StyledBackground, True)
        self.workspace.setMouseTracking(True)  # ✅ 启用鼠标追踪
        # ✅ 关键：给 workspace 设置 1 的权重，让它吞掉所有剩余高度
        self.v_layout.addWidget(self.workspace, 1)

        # 4. 初始化绝对定位组件 (不要加进 layout)
        self.content_stack = QStackedWidget(self.workspace)
        self.content_stack.setObjectName("ContentStack")
        self.content_stack.setAttribute(Qt.WA_StyledBackground, True)
        
        self.nav_rail = QFrame(self.workspace)
        self.nav_rail.setObjectName("NavRail")
        self.nav_rail.setAttribute(Qt.WA_StyledBackground, True)
        
        # 提升层级，确保在 stack 上方
        self.nav_rail.raise_()
        
    def _init_nav_content(self):
        """初始化导航栏内容（按钮等）"""
        # 导航栏布局
        nav_layout = QVBoxLayout(self.nav_rail)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(5)
        
        # 顶部留白
        nav_layout.addSpacing(10)
        
        # 导航按钮菜单（使用 SVG 图标）
        menu = [
            ("battle.svg", "野怪一览"),
            ("scanner.svg", "卡牌识别"),
            ("chest.svg", "手头物品"),
            ("search.svg", "百科搜索"),
            ("history.svg", "历史战绩"),
        ]
        
        # ========== 🎨 SVG 图标配置区域（手动调整） ==========
        icon_size = int(40 * self.current_scale)  # 图标大小（像素）
        normal_color = "#ffffff"  # 默认白色（未选中状态）
        active_color = "#f59e0b"  # 选中颜色（琥珀金）
        # ===================================================
        
        # 创建按钮组实现互斥选中
        self.nav_button_group = QButtonGroup(self)
        self.nav_button_group.setExclusive(True)
        
        for i, (icon_file, text) in enumerate(menu):
            btn = QPushButton()
            btn.setProperty("class", "NavButton")
            btn.setCheckable(True)
            btn.setChecked(i == 0)  # 默认选中第一个
            btn.setCursor(Qt.PointingHandCursor)
            
            # 存储图标文件路径和文本
            icon_path = os.path.join("assets", "icon", icon_file)
            btn.icon_path = icon_path
            btn.label_text = text
            
            # 创建图标（第一个按钮用选中颜色，其他用默认颜色）
            color = active_color if i == 0 else normal_color
            icon = create_colored_svg_icon(icon_path, color, icon_size)
            btn.setIcon(icon)
            btn.setIconSize(QSize(icon_size, icon_size))
            
            # 固定高度，宽度在 update_nav_button_sizes 中设置
            btn.setFixedHeight(52)
            
            btn.clicked.connect(lambda _, idx=i: self._on_nav_clicked(idx))
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)
            self.nav_button_group.addButton(btn, i)  # 添加到按钮组
        
        # 中间弹性空间
        nav_layout.addStretch()
        
        # 底部留白
        nav_layout.addSpacing(10)
        
        # 设置按钮
        self.settings_btn = QPushButton()
        self.settings_btn.setProperty("class", "NavButton")
        self.settings_btn.setCheckable(True)  # ✅ 设置为可选中
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        
        # 使用 setting.svg 图标
        setting_icon_path = os.path.join("assets", "icon", "setting.svg")
        self.settings_btn.icon_path = setting_icon_path
        self.settings_btn.label_text = "系统设置"
        
        # 创建图标（使用和导航按钮相同的大小和颜色配置）
        icon = create_colored_svg_icon(setting_icon_path, normal_color, icon_size)
        self.settings_btn.setIcon(icon)
        self.settings_btn.setIconSize(QSize(icon_size, icon_size))
        
        self.settings_btn.setFixedHeight(52)
        self.settings_btn.clicked.connect(self._on_settings_clicked)
        nav_layout.addWidget(self.settings_btn)
        
        # 底部留白
        nav_layout.addSpacing(10)
    
    def _init_pages(self):
        """初始化内容页面"""
        # 1. 野怪一览页面
        self.monster_page = MonsterOverviewPage()
        self.content_stack.addWidget(self.monster_page)
        
        # 2. 卡牌识别页面 (占位)
        scanner_placeholder = QLabel("卡牌识别 - 待实现")
        scanner_placeholder.setAlignment(Qt.AlignCenter)
        scanner_placeholder.setStyleSheet("color: #888; font-size: 16pt;")
        self.content_stack.addWidget(scanner_placeholder)
        
        # 3. 手头物品页面 (占位)
        items_placeholder = QLabel("手头物品 - 待实现")
        items_placeholder.setAlignment(Qt.AlignCenter)
        items_placeholder.setStyleSheet("color: #888; font-size: 16pt;")
        self.content_stack.addWidget(items_placeholder)
        
        # 4. 百科搜索页面
        self.encyclopedia_page = EncyclopediaPage()
        self.content_stack.addWidget(self.encyclopedia_page)
        
        # 5. 历史战绩页面
        self.history_page = HistoryPage()
        self.content_stack.addWidget(self.history_page)
        
        # 6. ✅ 设置页面（真实页面，替换占位符）
        self.settings_page = SettingsPage()
        self.content_stack.addWidget(self.settings_page)
        
        # 绑定设置页面的信号
        self.settings_page.scale_changed.connect(self._on_settings_scale_changed)
        self.settings_page.language_changed.connect(self._on_settings_language_changed)
        
        # 默认显示第一个页面（野怪一览）
        self.content_stack.setCurrentIndex(0)
    
    def _init_animations(self):
        """初始化导航栏展开/收起动画"""
        self.nav_anim = QPropertyAnimation(self.nav_rail, b"minimumWidth")
        self.nav_anim.setDuration(250)
        self.nav_anim.setEasingCurve(QEasingCurve.OutCubic)
        # 同步最大宽度
        self.nav_anim.valueChanged.connect(lambda v: self.nav_rail.setMaximumWidth(v))
        
        # 绑定鼠标进入/离开事件
        self.nav_rail.enterEvent = self._on_nav_enter
        self.nav_rail.leaveEvent = self._on_nav_leave
    
    def _on_nav_enter(self, event):
        """鼠标进入导航栏 - 展开"""
        target_w = int(styles.NAV_WIDTH_EXPANDED * self.current_scale)
        self.nav_anim.stop()
        self.nav_anim.setEndValue(target_w)
        self.nav_anim.start()
        
        # 显示文字标签
        for btn in self.nav_buttons:
            btn.setText(btn.label_text)
        self.settings_btn.setText(self.settings_btn.label_text)
    
    def _on_nav_leave(self, event):
        """鼠标离开导航栏 - 收起"""
        target_w = int(styles.NAV_WIDTH_COLLAPSED * self.current_scale)
        self.nav_anim.stop()
        self.nav_anim.setEndValue(target_w)
        self.nav_anim.start()
        
        # 隐藏文本（只显示图标）
        for btn in self.nav_buttons:
            btn.setText("")
        self.settings_btn.setText("")
    
    def _on_nav_clicked(self, index):
        """导航按钮点击"""
        # ========== 🎨 点击状态颜色配置（手动调整） ==========
        icon_size = int(40 * self.current_scale)  # 与初始化保持一致
        normal_color = "#ffffff"  # 未选中颜色（白色）
        active_color = "#f59e0b"   # 选中颜色（琥珀金）
        # ===================================================
        
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
            # 更新图标颜色
            color = active_color if i == index else normal_color
            icon = create_colored_svg_icon(btn.icon_path, color, icon_size)
            btn.setIcon(icon)
        
        # ✅ 取消设置按钮的选中状态
        self.settings_btn.setChecked(False)
        icon = create_colored_svg_icon(self.settings_btn.icon_path, normal_color, icon_size)
        self.settings_btn.setIcon(icon)
        
        # ✅ 切换内容区页面
        self.content_stack.setCurrentIndex(index)
        print(f"[Nav] Switched to page {index}")
    
    def update_nav_button_sizes(self):
        """更新所有导航按钮的宽度（根据当前展开状态）"""
        # 展开时的宽度
        expanded_w = int(styles.NAV_WIDTH_EXPANDED * self.current_scale)
        
        for btn in self.nav_buttons:
            btn.setFixedWidth(expanded_w)
        self.settings_btn.setFixedWidth(expanded_w)
    
    def _update_nav_icons(self):
        """更新导航栏图标大小（根据当前缩放比例）"""
        icon_size = int(40 * self.current_scale)
        normal_color = "#ffffff"
        active_color = "#f59e0b"
        
        # 更新导航按钮图标
        for i, btn in enumerate(self.nav_buttons):
            color = active_color if btn.isChecked() else normal_color
            icon = create_colored_svg_icon(btn.icon_path, color, icon_size)
            btn.setIcon(icon)
            btn.setIconSize(QSize(icon_size, icon_size))
        
        # 更新设置按钮图标
        icon = create_colored_svg_icon(self.settings_btn.icon_path, normal_color, icon_size)
        self.settings_btn.setIcon(icon)
        self.settings_btn.setIconSize(QSize(icon_size, icon_size))
    
    def _layout_components(self):
        """
        根据 workspace 的实时大小，手动刷新子控件的几何位置
        """
        # 如果控件还没完全初始化好，直接返回
        if not hasattr(self, 'nav_rail') or not self.workspace.isVisible():
            # 即使不可见，初次计算也需要一个基础值，我们可以强制刷新一下布局
            self.v_layout.activate()

        # 获取当前工作区的实际几何矩形
        rect = self.workspace.rect()
        if rect.height() < 10: return # 还没拉伸好

        scale = self.current_scale
        cw = int(styles.NAV_WIDTH_COLLAPSED * scale)

        # ✅ 修正：让 nav_rail 严格填满 workspace，应用缩放
        # y=0, x=0 开始，高度等于 rect.height()
        self.nav_rail.setGeometry(0, 0, cw, rect.height())
        
        # ✅ 同时更新导航栏的最小/最大宽度（应用缩放）
        self.nav_rail.setMinimumWidth(cw)
        self.nav_rail.setMaximumWidth(cw)
        
        # 内容区紧随其后
        self.content_stack.setGeometry(cw, 0, rect.width() - cw, rect.height())

    def update_ui_scale(self, scale):
        self.current_scale = scale
        
        # ✅ 暂停保存，防止缩放时抖动
        self._is_scaling = True
        
        # ✅ 不再改变窗口大小，只更新内部组件的缩放
        # 注释掉窗口大小调整
        # new_w, new_h = int(500 * scale), int(700 * scale)
        # self.resize(new_w, new_h)
        
        # 更新样式
        self.setStyleSheet(styles.get_sidebar_style(scale))
        
        # 更新标题栏高度
        self.title_bar.setFixedHeight(int(styles.TITLE_BAR_HEIGHT * scale))
        
        # 更新导航按钮尺寸和图标
        if hasattr(self, 'nav_buttons'):
            self.update_nav_button_sizes()
            self._update_nav_icons()  # ✅ 更新图标大小
        
        # ✅ 更新设置页面的缩放（如果存在）
        if hasattr(self, 'settings_page'):
            self.settings_page.update_scale(scale)
        
        # ✅ 强制重新布局
        self._layout_components()
        
        # ✅ 恢复保存
        self._is_scaling = False

    def resizeEvent(self, event):
        """
        这是绝对定位的灵魂：窗口只要变大变小，立刻重算子组件位置
        ✅ 同时保存窗口大小（缩放时不保存）
        """
        super().resizeEvent(event)
        self._layout_components()
        
        # 保存窗口几何信息（只在窗口可见且不在缩放过程中时）
        if self.isVisible() and not self._is_scaling:
            self._save_window_geometry()
    
    def moveEvent(self, event):
        """
        ✅ 窗口移动时保存位置（使用防抖）
        """
        super().moveEvent(event)
        
        # 每次移动时启动防抖定时器（不产生日志）
        if self.isVisible():
            self._save_window_geometry()

    def closeEvent(self, event):
        """窗口关闭时立即保存位置"""
        self._save_window_geometry_now()
        super().closeEvent(event)

    def _on_lang_clicked(self):
        """语言切换按钮点击"""
        current_lang = self.i18n.get_language()
        
        # 循环切换：简中 → 繁中 → 英文 → 简中
        if current_lang == "zh_CN":
            self.i18n.set_language("zh_TW")
            self.lang_btn.setText("🌐 繁中")
        elif current_lang == "zh_TW":
            self.i18n.set_language("en_US")
            self.lang_btn.setText("🌐 EN")
        else:
            self.i18n.set_language("zh_CN")
            self.lang_btn.setText("🌐 简中")
        
        # 更新所有页面的语言
        if hasattr(self, 'monster_page'):
            self.monster_page.update_language()
        
        print(f"[Language] Switched to {self.i18n.get_language()}")
    
    def _on_settings_clicked(self):
        """设置按钮点击 - 跳转到设置页面"""
        # 切换到设置页面（索引 5）
        self.content_stack.setCurrentIndex(5)
        
        # 更新导航按钮状态（取消所有选中）
        icon_size = int(40 * self.current_scale)
        normal_color = "#ffffff"
        active_color = "#f59e0b"
        
        for btn in self.nav_buttons:
            btn.setChecked(False)
            icon = create_colored_svg_icon(btn.icon_path, normal_color, icon_size)
            btn.setIcon(icon)
        
        # ✅ 设置按钮设置为选中状态（金色图标）
        self.settings_btn.setChecked(True)
        icon = create_colored_svg_icon(self.settings_btn.icon_path, active_color, icon_size)
        self.settings_btn.setIcon(icon)
        
        print("[Settings] Opened settings page")
    
    def _on_settings_scale_changed(self, scale):
        """设置页面的缩放改变"""
        self.update_ui_scale(scale)
        print(f"[Settings] UI scale changed to {scale}")
    
    def _on_settings_language_changed(self, lang_code):
        """设置页面的语言改变"""
        self.i18n.set_language(lang_code)
        
        # 更新顶部语言按钮显示
        lang_map = {
            "zh_CN": "🌐 简中",
            "zh_TW": "🌐 繁中",
            "en_US": "🌐 EN"
        }
        self.lang_btn.setText(lang_map.get(lang_code, "🌐 简中"))
        
        # 更新所有页面的语言
        if hasattr(self, 'monster_page'):
            self.monster_page.update_language()
        if hasattr(self, 'encyclopedia_page'):
            self.encyclopedia_page.update_language()
        
        print(f"[Settings] Language changed to {lang_code}")
    
    def enterEvent(self, event):
        """鼠标进入窗口"""
        # 取消延迟收起
        self.leave_timer.stop()
        
        # 如果已收起，展开窗口
        if self.is_auto_collapsed:
            self._trigger_auto_expand()
        
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开窗口"""
        # 启动延迟检查
        self.leave_timer.start(self.leave_delay)
        super().leaveEvent(event)
    
    def _check_auto_collapse(self):
        """检查是否应该自动收起"""
        # 检查详情窗口是否显示且鼠标在其上
        if hasattr(self, 'monster_page') and self.monster_page.detail_window:
            detail_win = self.monster_page.detail_window
            if detail_win.isVisible():
                # 检查鼠标是否在详情窗口上
                from PySide6.QtGui import QCursor
                cursor_pos = QCursor.pos()
                if detail_win.geometry().contains(cursor_pos):
                    # 鼠标在详情窗口上，不收起
                    return
        
        # 只有当窗口在屏幕最上方时才自动收起
        if self._is_at_screen_top():
            self._trigger_auto_collapse()
    
    def _is_at_screen_top(self):
        """检查窗口是否在屏幕最上方"""
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().availableGeometry()
        # 如果窗口顶部在屏幕顶部附近（10px以内），认为是在顶部
        return self.y() <= screen.y() + 10
    
    def _trigger_auto_collapse(self):
        """触发收起动画 - 向上收起到屏幕顶部"""
        from PySide6.QtCore import QPropertyAnimation, QEasingCurve
        from PySide6.QtWidgets import QApplication
        
        # 获取当前窗口位置和大小
        current_pos = self.pos()
        current_size = self.size()
        
        # 获取屏幕信息
        screen = QApplication.primaryScreen().availableGeometry()
        
        # 计算目标高度 - 1px，向上移出屏幕
        collapsed_height = 1
        
        # 创建几何动画
        self.collapse_anim = QPropertyAnimation(self, b"geometry")
        self.collapse_anim.setDuration(400)
        self.collapse_anim.setEasingCurve(QEasingCurve.InOutCubic)
        
        # 向上收起：Y坐标移到屏幕顶部减去窗口高度，只露出1px
        target_rect = QRect(
            current_pos.x(),
            screen.top() - current_size.height() + collapsed_height,
            current_size.width(),
            current_size.height()
        )
        
        self.collapse_anim.setEndValue(target_rect)
        self.collapse_anim.start()
        
        # 标记为已收起状态
        self.is_auto_collapsed = True
        
        # 保存收起前的几何信息
        self._pre_collapse_geometry = QRect(current_pos, current_size)
    
    def _trigger_auto_expand(self):
        """触发展开动画 - 从顶部展开"""
        from PySide6.QtCore import QPropertyAnimation, QEasingCurve
        
        if not self.is_auto_collapsed or not hasattr(self, '_pre_collapse_geometry'):
            return
        
        # 创建展开动画
        self.expand_anim = QPropertyAnimation(self, b"geometry")
        self.expand_anim.setDuration(400)
        self.expand_anim.setEasingCurve(QEasingCurve.InOutCubic)
        self.expand_anim.setEndValue(self._pre_collapse_geometry)
        self.expand_anim.start()
        
        # 取消收起状态
        self.is_auto_collapsed = False
    
    def _position_to_right(self):
        """测试用：将窗口移动到屏幕右侧"""
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.width() - 20, (screen.height() - self.height()) // 2)

    def _load_window_geometry(self):
        """加载保存的窗口位置和大小"""
        from PySide6.QtWidgets import QApplication
        
        # 尝试从 JSON 文件加载
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.debug(f"Loaded sidebar config: {config}")
                    
                width = config.get("window_width", 500)
                height = config.get("window_height", 700)
                
                # 确保在合理范围内
                width = max(self.minimumWidth(), min(self.maximumWidth(), width))
                height = max(self.minimumHeight(), min(self.maximumHeight(), height))
                
                self.resize(width, height)
                
                # 加载位置
                has_pos = config.get("has_position", False)
                if has_pos:
                    x = config.get("window_x", -1)
                    y = config.get("window_y", -1)
                    logger.debug(f"Attempting to restore position x={x}, y={y}, width={width}, height={height}")
                    
                    if x >= 0 and y >= 0:
                        # 验证位置是否在任意屏幕范围内
                        screens = QApplication.screens()
                        found = False
                        for s in screens:
                            screen = s.availableGeometry()
                            logger.debug(f"Checking screen: left={screen.left()}, top={screen.top()}, right={screen.right()}, bottom={screen.bottom()}")
                            if (x >= screen.left() and x + width <= screen.right() + 100 and
                                y >= screen.top() and y + height <= screen.bottom() + 100):
                                logger.debug(f"Restoring sidebar geometry to ({x},{y},{width},{height}) on screen")
                                self.move(x, y)
                                found = True
                                break
                        if found:
                            return
                        else:
                            logger.debug("Saved position does not fit any screen bounds, falling back to default position")
        except Exception as e:
            logger.debug(f"加载窗口配置失败: {e}")
        
        # 如果没有保存的位置或位置无效，使用默认位置（右侧）
        self.resize(500, 700)
        self._position_to_right()

    def _save_window_geometry(self):
        """保存当前窗口位置和大小（防抖）
        改动：只排队保存，不产生日志，实际写入时再记录。
        """
        # 不在自动收起动画过程中保存（避免负y坐标等脏数据）
        if getattr(self, 'is_auto_collapsed', False) and getattr(self, '_pre_collapse_geometry', None) is None:
            # 如果已经收起但没有 pre-collapse 数据，跳过
            return

        # 如果已经有保存任务在排队，则只重启定时器
        if self._save_pending:
            self.save_timer.start()
            return

        # 标记为待保存并启动定时器（不产生日志）
        self._save_pending = True
        self.save_timer.start()

    def _save_window_geometry_now(self):
        """立即保存当前窗口位置和大小到 JSON 文件（实际写入）"""
        try:
            import time
            now = time.time()
            # 重置 pending 标记
            self._save_pending = False

            # 限制最小保存间隔，防止动画抖动或连续操作频繁写盘
            if now - getattr(self, '_last_saved_time', 0.0) < getattr(self, '_min_save_interval', 2.0):
                logger.debug(f"Skipping save due to min interval. last_saved={self._last_saved_time}, now={now}")
                return

            # 如果处于自动收起状态，优先保存收起前的位置
            if getattr(self, 'is_auto_collapsed', False) and hasattr(self, '_pre_collapse_geometry'):
                geom = self._pre_collapse_geometry
                x, y, w, h = geom.x(), geom.y(), geom.width(), geom.height()
                logger.debug(f"Saving pre-collapse geometry: x={x}, y={y}, w={w}, h={h}")
            else:
                x, y, w, h = self.x(), self.y(), self.width(), self.height()
                logger.debug(f"Saving current geometry: x={x}, y={y}, w={w}, h={h}")

            # 设置最后保存时间，避免并发/重复写入
            self._last_saved_time = now

            config = {
                "window_width": w,
                "window_height": h,
                "window_x": x,
                "window_y": y,
                "has_position": True
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.debug(f"Sidebar geometry saved to {self.config_file}: {config}")
        except Exception as e:
            logger.debug(f"保存窗口配置失败: {e}")
    
# 运行测试
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = SidebarWindow()
    # ✅ 不需要手动定位，_load_window_geometry() 会自动处理
    # 如果没有保存的位置，会自动调用 _position_to_right()
    window.show() # show 会触发第一次 resizeEvent
    sys.exit(app.exec())