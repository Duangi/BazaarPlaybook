import sys
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QStackedWidget, QButtonGroup)
from PySide6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, Signal, QSize
from PySide6.QtGui import QIcon
import gui.styles as styles
from gui.utils.frameless_helper import FramelessHelper
from utils.icon_helper import create_colored_svg_icon
from gui.pages.monster_overview_page import MonsterOverviewPage
from utils.i18n import get_i18n

class SidebarWindow(QWidget):
    collapse_to_island = Signal()  # 收起到灵动岛信号
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 设置窗口尺寸限制（必须在创建 FramelessHelper 之前设置）
        self.setMinimumSize(400, 500)
        self.setMaximumSize(800, 1200)
        
        # ✅ 启用完整的拖拽和8方向调整大小功能
        self.frameless_helper = FramelessHelper(
            self, 
            margin=5,           # 边缘检测区域 5px（更精确的边缘检测）
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
        
        title_layout.addStretch()
        
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
        self.settings_btn.clicked.connect(lambda: print("[Settings] Clicked"))
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
        
        # 4. 百科搜索页面 (占位)
        search_placeholder = QLabel("百科搜索 - 待实现")
        search_placeholder.setAlignment(Qt.AlignCenter)
        search_placeholder.setStyleSheet("color: #888; font-size: 16pt;")
        self.content_stack.addWidget(search_placeholder)
        
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

        # ✅ 修正：让 nav_rail 严格填满 workspace
        # y=0, x=0 开始，高度等于 rect.height()
        self.nav_rail.setGeometry(0, 0, cw, rect.height())
        
        # 内容区紧随其后
        self.content_stack.setGeometry(cw, 0, rect.width() - cw, rect.height())

    def update_ui_scale(self, scale):
        self.current_scale = scale
        # 更新窗口物理尺寸（使用 resize 而不是 setFixedSize，以支持调整大小）
        new_w, new_h = int(500 * scale), int(700 * scale)
        self.resize(new_w, new_h)
        # 更新样式
        self.setStyleSheet(styles.get_sidebar_style(scale))
        # 更新标题栏高度
        self.title_bar.setFixedHeight(int(styles.TITLE_BAR_HEIGHT * scale))
        # 更新导航按钮尺寸
        if hasattr(self, 'nav_buttons'):
            self.update_nav_button_sizes()
        # 此时不要直接算位置，等 resizeEvent 触发

    def resizeEvent(self, event):
        """
        这是绝对定位的灵魂：窗口只要变大变小，立刻重算子组件位置
        """
        super().resizeEvent(event)
        self._layout_components()
    
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
    
    def _position_to_right(self):
        """测试用：将窗口移动到屏幕右侧"""
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.width() - 20, (screen.height() - self.height()) // 2)

# 运行测试
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = SidebarWindow()
    window._position_to_right()
    window.show() # show 会触发第一次 resizeEvent
    sys.exit(app.exec())