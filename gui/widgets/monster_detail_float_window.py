"""
怪物详情悬浮窗 (Monster Detail Float Window)
在主窗口旁边显示的独立悬浮窗口
"""
import os
import json
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QWidgetItem
from PySide6.QtCore import Qt, Signal, QTimer, QSize, QSettings
from PySide6.QtGui import QPixmap
from data_manager.monster_loader import Monster
from utils.i18n import get_i18n
from utils.image_loader import ImageLoader, CardSize
from gui.widgets.item_detail_card import ItemDetailCard
from gui.styles import SCROLLBAR_STYLE
from gui.utils.frameless_helper import FramelessHelper


from utils.window_utils import get_foreground_window_title, restore_focus_to_game

class MonsterDetailFloatWindow(QWidget):
    """
    怪物详情悬浮窗
    - 显示在主窗口旁边
    - 鼠标悬浮触发显示
    - 鼠标离开延迟隐藏
    """

    closed = Signal()  # 关闭信号

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # --- Focus Tracking ---
        self.last_focused_window = None
        # ----------------------

        self.current_monster = None
        self.current_item_id = None
        self.display_mode = 'monster'
        self.i18n = get_i18n()
        # track a single active item popup to avoid overlapping popups
        self._active_item_popup = None
        
        # 用于记住窗口大小和内容缩放比例
        self.settings = QSettings("Reborn", "MonsterDetailWindow")
        
        # ✅ 内容缩放比例（默认1.0，范围0.5-2.0）
        self.content_scale = self.settings.value("content_scale", 1.0, type=float)
        self.content_scale = max(0.5, min(2.0, self.content_scale))  # 限制范围
        
        # 缩放拖动状态
        self._scaling = False
        self._scale_start_pos = None
        self._scale_start_scale = 1.0

        # 延迟关闭定时器
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.setInterval(300)  # 300ms 延迟
        self.hide_timer.timeout.connect(self._delayed_hide)

        self.setMouseTracking(True)

        self._init_window()
        self._init_ui()
        
        # ✅ 初始化可调整大小的辅助工具
        self.frameless_helper = FramelessHelper(
            self,
            margin=5,           # 边缘检测区域
            snap_to_top=False,  # 不吸附顶部
            enable_drag=True,   # ✅ 启用拖拽
            enable_resize=True, # ✅ 启用调整大小
            debug=False
        )
        
        # 加载保存的窗口状态
        self._load_window_state()
        
        # ✅ 创建缩放手柄（右下角）
        self._create_scale_handle()
    def closeEvent(self, event):
        """窗口关闭时保存状态"""
        self._save_window_state()
        super().closeEvent(event)

    def mouseReleaseEvent(self, event):
        """鼠标释放时保存位置 (拖拽结束)"""
        super().mouseReleaseEvent(event)
        self._save_window_state()

    def _save_window_state(self):
        """保存窗口位置和大小"""
        self.settings.setValue("pos", self.pos())
        self.settings.setValue("size", self.size())
        self.settings.setValue("content_scale", self.content_scale)

    def _load_window_state(self):
        """加载窗口位置和大小"""
        # 恢复大小
        size = self.settings.value("size", QSize(400, 600))
        self.resize(size)
        
        # 恢复位置 (如果有保存，且在屏幕范围内)
        pos = self.settings.value("pos")
        if pos:
            self.move(pos)
        else:
            # 默认居中
            self.reset_position()

    def reset_position(self):
        """重置位置到屏幕中心"""
        screen = self.screen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x + screen.left(), y + screen.top())
        self._save_window_state()

    def _init_window(self):
        """初始化窗口属性"""
        # 独立的悬浮窗口
        self.setWindowFlags(
            Qt.WindowType.Tool |  # 工具窗口，不在任务栏显示
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)  # 显示时不激活焦点
        
        # ✅ 设置可调整大小的范围（不再固定大小）
        self.setMinimumSize(360, 400)
        self.setMaximumSize(800, 1200)
        # 默认大小（会被 _load_window_size 覆盖）
        self.resize(400, 600)

    def _init_ui(self):
        """初始化 UI"""
        print("[DEBUG] _init_ui started")
        try:
            # 根布局
            root_layout = QVBoxLayout(self)
            root_layout.setContentsMargins(0, 0, 0, 0)

            print("[DEBUG] creating main_container")
            # 主容器（带金色边框）
            self.main_container = QFrame()
            self.main_container.setObjectName("FloatWindow")
            self.main_container.setStyleSheet("""
                #FloatWindow {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(10, 10, 12, 0.95),
                        stop:1 rgba(5, 5, 8, 0.95));
                    border-right: 2px solid #f59e0b;
                    border-radius: 8px;
                }
            """)
            root_layout.addWidget(self.main_container)

            # 主容器布局
            container_layout = QVBoxLayout(self.main_container)
            container_layout.setContentsMargins(15, 15, 15, 15)
            container_layout.setSpacing(12)

            print("[DEBUG] creating scroll")
            # 滚动区域
            self.scroll = QScrollArea()
            self.scroll.setWidgetResizable(True)
            self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            # 使用共享滚动样式
            self.scroll.setStyleSheet(SCROLLBAR_STYLE + "QScrollArea { border: none; background: transparent; }")

            self.content_widget = QWidget()
            self.content_widget.setStyleSheet("background: transparent;")
            self.content_layout = QVBoxLayout(self.content_widget)
            self.content_layout.setSpacing(10)
            self.content_layout.setContentsMargins(0, 0, 0, 0)
            
            print("[DEBUG] content_layout created:", self.content_layout)

            self.scroll.setWidget(self.content_widget)
            container_layout.addWidget(self.scroll)
            print("[DEBUG] _init_ui finished")
        except Exception as e:
            print(f"[ERROR] _init_ui failed: {e}")
            import traceback
            traceback.print_exc()

    def _load_window_size(self):
        """加载保存的窗口大小"""
        width = self.settings.value("window_width", 400, type=int)
        height = self.settings.value("window_height", 600, type=int)
        
        # 确保在合理范围内
        width = max(self.minimumWidth(), min(self.maximumWidth(), width))
        height = max(self.minimumHeight(), min(self.maximumHeight(), height))
        
        self.resize(width, height)
    
    def _save_window_size(self):
        """保存当前窗口大小"""
        self.settings.setValue("window_width", self.width())
        self.settings.setValue("window_height", self.height())
    
    def resizeEvent(self, event):
        """
        窗口大小改变时：
        1. 保存新的大小
        2. 重新定位以保持与sidebar紧贴
        3. 更新缩放手柄位置
        """
        super().resizeEvent(event)
        
        # ✅ 更新缩放手柄位置
        self._update_scale_handle_position()
        
        # 只在窗口可见且有锚点时处理
        if self.isVisible() and hasattr(self, '_anchor_widget') and self._anchor_widget:
            # 保存大小
            self._save_window_size()
            
            # ✅ 重新计算位置以保持紧贴
            from PySide6.QtWidgets import QApplication
            screen = QApplication.primaryScreen().availableGeometry()
            anchor_global_pos = self._anchor_widget.mapToGlobal(self._anchor_widget.rect().topLeft())
            anchor_height = self._anchor_widget.height()
            
            # 计算垂直居中位置
            y = anchor_global_pos.y() + (anchor_height - self.height()) // 2
            
            # 根据展开方向重新计算X位置
            if self._on_left_side:
                # 紧贴右侧
                x = anchor_global_pos.x() + self._anchor_widget.width()
            else:
                # 紧贴左侧
                x = anchor_global_pos.x() - self.width()
            
            # 确保不超出屏幕
            if x < screen.left():
                x = screen.left() + 10
            if x + self.width() > screen.right():
                x = screen.right() - self.width() - 10
            if y < screen.top():
                y = screen.top() + 10
            if y + self.height() > screen.bottom():
                y = screen.bottom() - self.height() - 10
            
            # 移动到新位置
            self.move(x, y)
    
    def show_floating(self, monster):
        """
        显示浮动详情 (使用保存的位置或默认位置)
        """
        self.display_mode = 'monster'
        self.current_monster = monster
        self._update_content()
        
        # 恢复位置
        self._load_window_state()
        
        self.show()
        self.raise_()

    def show_item_beside(self, anchor_widget, item_id):
        """
        显示物品详情在指定窗口旁边
        """
        self.display_mode = 'item'
        self.current_item_id = item_id
        self._update_content()
        self._position_beside(anchor_widget)

    def show_beside(self, anchor_widget, monster):
        """
        显示在指定窗口旁边（自动选择左侧或右侧）
        ✅ 调整大小后仍保持紧贴sidebar
        """
        self.display_mode = 'monster'
        self.current_monster = monster
        self._update_content()
        self._position_beside(anchor_widget)

    def _position_beside(self, anchor_widget):
        from PySide6.QtWidgets import QApplication

        # 获取屏幕和窗口信息
        screen = QApplication.primaryScreen().availableGeometry()
        anchor_global_pos = anchor_widget.mapToGlobal(anchor_widget.rect().topLeft())
        anchor_center_x = anchor_global_pos.x() + anchor_widget.width() // 2
        anchor_height = anchor_widget.height()

        # 判断窗口在屏幕的哪一侧
        screen_center_x = screen.center().x()
        on_left_side = anchor_center_x < screen_center_x
        
        # ✅ 保存当前的展开方向，用于后续调整大小时重新定位
        self._anchor_widget = anchor_widget
        self._on_left_side = on_left_side

        # 计算垂直位置（居中对齐）
        y = anchor_global_pos.y() + (anchor_height - self.height()) // 2

        # 根据窗口位置选择展开方向并计算X位置
        if on_left_side:
            # 窗口在左侧，向右展开（显示在右侧，紧贴）
            x = anchor_global_pos.x() + anchor_widget.width()
            # 更新边框样式（左边框）
            self.main_container.setStyleSheet("""
                #FloatWindow {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(10, 10, 12, 0.95),
                        stop:1 rgba(5, 5, 8, 0.95));
                    border-left: 2px solid #f59e0b;
                    border-radius: 8px;
                }
            """)
        else:
            # 窗口在右侧，向左展开（显示在左侧，紧贴）
            x = anchor_global_pos.x() - self.width()
            # 更新边框样式（右边框）
            self.main_container.setStyleSheet("""
                #FloatWindow {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(10, 10, 12, 0.95),
                        stop:1 rgba(5, 5, 8, 0.95));
                    border-right: 2px solid #f59e0b;
                    border-radius: 8px;
                }
            """)

        # 确保不超出屏幕边界
        if x < screen.left():
            x = screen.left() + 10
        if x + self.width() > screen.right():
            x = screen.right() - self.width() - 10
        if y < screen.top():
            y = screen.top() + 10
        if y + self.height() > screen.bottom():
            y = screen.bottom() - self.height() - 10

        self.move(x, y)
        self.show()
        self.raise_()

        # 停止隐藏定时器
        self.hide_timer.stop()

    def _update_content(self):
        """更新详情内容"""
        # 清空旧内容
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if self.display_mode == 'item' and self.current_item_id:
             scale = self.content_scale
             # Create ItemDetailCard
             item_card = ItemDetailCard(item_id=self.current_item_id, item_type="item",
                                        default_expanded=True, enable_tier_click=True, content_scale=scale)
             self.content_layout.addWidget(item_card)
             return

        if not self.current_monster:
            return

        m = self.current_monster
        lang = self.i18n.get_language()
        
        # ✅ 应用缩放比例到字体大小
        scale = self.content_scale

        # 1. 怪物头像 + 基础信息
        header_card = QFrame()
        header_card.setStyleSheet("background: transparent; border: none;")
        header_layout = QHBoxLayout(header_card)
        header_layout.setSpacing(int(12 * scale))
        header_layout.setContentsMargins(0, 0, 0, 0)

        # 怪物头像
        avatar_label = QLabel()
        avatar_size = int(56 * scale)
        avatar_label.setFixedSize(avatar_size, avatar_size)
        avatar_label.setStyleSheet("border: none; background: transparent;")
        pixmap = ImageLoader.load_monster_image(m.name_zh, size=avatar_size, with_border=True)
        avatar_label.setPixmap(pixmap)
        header_layout.addWidget(avatar_label)

        # 名字和血量
        info_layout = QVBoxLayout()
        info_layout.setSpacing(int(4 * scale))
        info_layout.addStretch()

        # 名字
        name_text = m.name_zh if lang == "zh_CN" else (m.name_tw if hasattr(m, 'name_tw') and m.name_tw else m.name_en)
        name_label = QLabel(name_text)
        name_label.setStyleSheet(f"font-size: {int(12 * scale)}pt; font-weight: bold; color: #f59e0b;")
        info_layout.addWidget(name_label)

        # 血量
        hp_label = QLabel(f"❤️ {m.health}")
        hp_label.setStyleSheet(f"font-size: {int(9 * scale)}pt; color: #ff6666;")
        info_layout.addWidget(hp_label)

        info_layout.addStretch()
        header_layout.addLayout(info_layout)

        self.content_layout.addWidget(header_card)

        # 2. 技能列表（分离主动/被动）
        if hasattr(m, 'skills') and m.skills:
            skills_label = QLabel("🎯 技能")
            skills_label.setStyleSheet(f"font-size: {int(10 * scale)}pt; font-weight: bold; color: #ffffff; margin-top: {int(6 * scale)}px;")
            self.content_layout.addWidget(skills_label)

            # If skill groups exist, try to separate
            for skill in m.skills:
                skill_id = skill.get("id", "")
                current_tier = skill.get("current_tier", "bronze").lower()  # ✅ 转换为小写确保匹配
                # ✅ 启用点击切换等级功能，并传入缩放比例
                skill_card = ItemDetailCard(skill_id, item_type="skill", current_tier=current_tier, 
                                           default_expanded=True, enable_tier_click=True, content_scale=scale)
                self.content_layout.addWidget(skill_card)

        # 3. 掉落物品（水平紧凑图标条）
        if hasattr(m, 'items') and m.items:
            loot_label = QLabel("💰 掉落")
            loot_label.setStyleSheet(f"font-size: {int(10 * scale)}pt; font-weight: bold; color: #ffffff; margin-top: {int(6 * scale)}px;")
            self.content_layout.addWidget(loot_label)

            # 容器
            loot_container = QFrame()
            loot_container.setStyleSheet("background: transparent; border: none;")
            loot_layout = QHBoxLayout(loot_container)
            # ✅ 应用缩放比例到间隔
            loot_layout.setSpacing(int(6 * scale))
            loot_layout.setContentsMargins(0, int(4 * scale), 0, 0)

            # tier -> color
            tier_colors = {
                'bronze': '#CD7F32',
                'silver': '#C0C0C0',
                'gold': '#FFD700',
                'diamond': '#B9F2FF'
            }

            # provide outer self for closure use in InlineItemLabel
            outer_self = self

            # Inline image widget class
            class InlineItemLabel(QLabel):
                def __init__(self, item_id, current_tier, tier_color, content_scale, card_size=CardSize.SMALL, parent=None, monster_item_data=None):
                    super().__init__(parent)
                    self.item_id = item_id
                    self.current_tier = current_tier  # ✅ 保存当前等级
                    self.tier_color = tier_color
                    self.content_scale = content_scale  # ✅ 保存缩放比例用于弹窗
                    self.monster_item_data = monster_item_data  # ✅ 保存怪物物品数据（包含enchantment）

                    # ✅ 应用缩放比例到图片尺寸
                    base_height = int(80 * content_scale)  # 统一高度（应用缩放）
                    border_w = max(2, int(3 * content_scale))  # 边框宽度（应用缩放，最小2px）
                    
                    # 根据卡牌尺寸决定宽度比例
                    if card_size == CardSize.SMALL:
                        img_w = int(base_height * 0.5)  # 40px (0.5倍)
                    elif card_size == CardSize.LARGE:
                        img_w = int(base_height * 1.5)  # 120px (1.5倍)
                    else:  # MEDIUM
                        img_w = base_height  # 80px (1倍)
                    
                    img_h = base_height

                    # 给 QLabel 留出边框的额外像素
                    total_w = img_w + border_w * 2
                    total_h = img_h + border_w * 2
                    self.setFixedSize(total_w, total_h)

                    # 使用样式化边框（不再在 ImageLoader 中添加边框）
                    self.setStyleSheet(f"border: {border_w}px solid {tier_color}; border-radius: 6px; background: transparent;")

                    # 加载卡牌图片（不带内置边框），并按计算尺寸缩放到内区域
                    pix = ImageLoader.load_card_image(item_id, card_size, height=img_h, with_border=False)
                    if not pix.isNull():
                        scaled = pix.scaled(img_w, img_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        self.setPixmap(scaled)

                    # 设置手型光标，提示可点击
                    self.setCursor(Qt.CursorShape.PointingHandCursor)

                    # popup
                    self._popup = None
                    # show delay to avoid instant pop when moving between icons
                    self._show_timer = QTimer(self)
                    self._show_timer.setSingleShot(True)
                    self._show_timer.setInterval(160)  # 160ms show delay
                    self._show_timer.timeout.connect(self._do_show_popup)

                    self._hide_timer = QTimer(self)
                    self._hide_timer.setSingleShot(True)
                    self._hide_timer.setInterval(300)
                    self._hide_timer.timeout.connect(self._hide_popup)
                
                def mousePressEvent(self, event):
                    """点击item图片时，切换所有技能描述的等级显示模式"""
                    # 切换弹窗中所有描述的等级显示
                    if self._popup and hasattr(self._popup, '_toggle_tier_display'):
                        self._popup._toggle_tier_display()
                    super().mousePressEvent(event)

                def _do_show_popup(self):
                    # hide any outer active popup first to avoid overlapping
                    try:
                        if outer_self._active_item_popup and outer_self._active_item_popup is not getattr(self, '_popup', None):
                            try:
                                outer_self._active_item_popup.hide()
                                outer_self._active_item_popup.deleteLater()
                            except Exception:
                                pass
                            outer_self._active_item_popup = None
                    except Exception:
                        pass

                    # ✅ 创建并直接展开详情（使用正确的 current_tier 和缩放比例）
                    # ✅ 如果有怪物物品数据（包含enchantment），需要将其与items_db数据合并
                    merged_item_data = None
                    if self.monster_item_data:
                        # 从 items_db 加载完整数据
                        try:
                            items_db_path = "assets/json/items_db.json"
                            if os.path.exists(items_db_path):
                                with open(items_db_path, 'r', encoding='utf-8') as f:
                                    items_db = json.load(f)
                                    db_item = next((i for i in items_db if i.get('id') == self.item_id), None)
                                    if db_item:
                                        # 合并：以items_db为基础，但保留monster数据中的enchantment
                                        merged_item_data = db_item.copy()
                                        if 'enchantment' in self.monster_item_data:
                                            merged_item_data['enchantment'] = self.monster_item_data['enchantment']
                        except Exception as e:
                            print(f"[Popup] Error merging item data: {e}")
                    
                    if self._popup is None:
                        self._popup = ItemDetailCard(self.item_id, item_type='item', current_tier=self.current_tier, 
                                                     default_expanded=True, enable_tier_click=True, content_scale=self.content_scale,
                                                     item_data=merged_item_data)  # ✅ 传入合并后的数据
                        # 设置为顶层窗口 - 移除 WA_ShowWithoutActivating 以允许激活
                        self._popup.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
                        
                        # 强制应用样式到顶层弹窗
                        try:
                            self._popup.setAttribute(Qt.WA_StyledBackground, True)
                            self._popup._setup_style()
                            self._popup.style().unpolish(self._popup)
                            self._popup.style().polish(self._popup)
                        except Exception as e:
                            print(f"[Popup] Style refresh error: {e}")
                        
                        # 动态计算宽度和高度：先让它自适应，然后限制范围
                        try:
                            # 允许内容自动调整大小，获取理想尺寸
                            self._popup.adjustSize()
                            ideal_size = self._popup.sizeHint()
                            
                            # 限制宽度：最小360，最大600，根据内容自适应
                            final_width = max(360, min(600, ideal_size.width()))
                            # 限制高度：最小200，最大600
                            final_height = max(200, min(600, ideal_size.height()))
                            
                            self._popup.setFixedSize(final_width, final_height)
                        except Exception:
                            # 如果动态计算失败，使用默认值
                            self._popup.setFixedSize(360, 400)

                    # register as active popup
                    outer_self._active_item_popup = self._popup

                    if self._hide_timer.isActive():
                        self._hide_timer.stop()
                    global_pos = self.mapToGlobal(self.rect().bottomLeft())
                    # 微调位置，优先向右展示，若超出屏幕则自动调整（QWidget.move 后系统会裁剪）
                    self._popup.move(global_pos.x(), global_pos.y()+6)
                    
                    # 显示并强制提升到最前面
                    self._popup.show()
                    self._popup.raise_()
                    self._popup.activateWindow()
                    # 额外设置：确保窗口在所有其他窗口之上
                    try:
                        from PySide6.QtWidgets import QApplication
                        QApplication.setActiveWindow(self._popup)
                    except Exception:
                        pass

                def enterEvent(self, event):
                    # cancel hide and start show timer
                    if self._hide_timer.isActive():
                        self._hide_timer.stop()
                    # start delayed show
                    self._show_timer.start()
                    super().enterEvent(event)

                def leaveEvent(self, event):
                    # cancel pending show, start hide timer
                    if self._show_timer.isActive():
                        self._show_timer.stop()
                    self._hide_timer.start()
                    super().leaveEvent(event)

                def _hide_popup(self):
                    if self._popup:
                        try:
                            self._popup.hide()
                            self._popup.deleteLater()
                        except Exception:
                            pass
                        # clear outer active if it points to this popup
                        try:
                            if outer_self._active_item_popup is self._popup:
                                outer_self._active_item_popup = None
                        except Exception:
                            pass
                        self._popup = None

            # add inline images
            for item in m.items:
                item_id = item.get('id', '')
                current_tier = item.get('current_tier', 'bronze').lower()  # ✅ 转换为小写确保匹配
                
                # 从items_db.json加载物品数据以获取正确的size
                try:
                    item_db_path = "assets/json/items_db.json"
                    if os.path.exists(item_db_path):
                        with open(item_db_path, 'r', encoding='utf-8') as f:
                            items_db = json.load(f)
                            item_data = next((i for i in items_db if i.get('id') == item_id), None)
                            if item_data:
                                size_str = item_data.get('size', 'Medium / 中型')
                                # 提取英文部分 "Large / 大型" -> "Large"
                                size_key = size_str.split('/')[0].strip().lower()
                            else:
                                size_key = 'medium'
                    else:
                        size_key = 'medium'
                except Exception as e:
                    print(f"[InlineItem] Failed to load size for {item_id}: {e}")
                    size_key = 'medium'
                
                # 根据size确定CardSize
                if 'large' in size_key:
                    cs = CardSize.LARGE
                elif 'small' in size_key:
                    cs = CardSize.SMALL
                else:
                    cs = CardSize.MEDIUM

                color = tier_colors.get(current_tier, '#CD7F32')
                # ✅ 传入 current_tier 和缩放比例参数，以及怪物物品数据
                label = InlineItemLabel(item_id, current_tier, color, scale, card_size=cs, monster_item_data=item)
                loot_layout.addWidget(label)

            # stretch to keep compact
            loot_layout.addStretch()
            self.content_layout.addWidget(loot_container)

        # 底部弹性空间
        self.content_layout.addStretch()

    def enterEvent(self, event):
        """鼠标进入 - 取消隐藏定时器"""
        self.hide_timer.stop()
        
        # Focus Tracking logic
        try:
            current_title = get_foreground_window_title()
            if current_title and "The Bazaar" in current_title: 
                self.last_focused_window = "The Bazaar"
            else:
                self.last_focused_window = None
        except:
            pass
            
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开 - 启动延迟隐藏"""
        self.hide_timer.start()
        
        # Restore focus
        if self.last_focused_window == "The Bazaar":
            restore_focus_to_game("The Bazaar")
            self.last_focused_window = None
            
        super().leaveEvent(event)

    def request_hide(self):
        """请求隐藏（从外部调用）"""
        self.hide_timer.start()

    def _delayed_hide(self):
        """延迟隐藏"""
        self.hide()
        self.closed.emit()

    def update_language(self):
        """更新语言"""
        if self.current_monster:
            self._update_content()

    def _create_scale_handle(self):
        """创建右下角的缩放手柄"""
        self.scale_handle = QLabel(self)
        self.scale_handle.setObjectName("ScaleHandle")
        self.scale_handle.setText("⇲")  # 对角线箭头
        self.scale_handle.setFixedSize(24, 24)
        self.scale_handle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scale_handle.setStyleSheet("""
            QLabel#ScaleHandle {
                background: rgba(245, 158, 11, 0.3);
                border: 1px solid rgba(245, 158, 11, 0.6);
                border-radius: 4px;
                color: #f59e0b;
                font-size: 14pt;
                font-weight: bold;
            }
            QLabel#ScaleHandle:hover {
                background: rgba(245, 158, 11, 0.5);
                border-color: #f59e0b;
            }
        """)
        self.scale_handle.setCursor(Qt.CursorShape.SizeFDiagCursor)
        self.scale_handle.setMouseTracking(True)
        
        # 安装事件过滤器来处理缩放拖动
        self.scale_handle.mousePressEvent = self._on_scale_press
        self.scale_handle.mouseMoveEvent = self._on_scale_move
        self.scale_handle.mouseReleaseEvent = self._on_scale_release
        
        # 初始位置（在 resizeEvent 中更新）
        self._update_scale_handle_position()
    
    def _update_scale_handle_position(self):
        """更新缩放手柄的位置（右下角）"""
        if hasattr(self, 'scale_handle'):
            x = self.width() - self.scale_handle.width() - 8
            y = self.height() - self.scale_handle.height() - 8
            self.scale_handle.move(x, y)
            self.scale_handle.raise_()  # 确保在最上层
    
    def _on_scale_press(self, event):
        """开始缩放拖动"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._scaling = True
            self._scale_start_pos = event.globalPosition().toPoint()
            self._scale_start_scale = self.content_scale
            event.accept()
    
    def _on_scale_move(self, event):
        """缩放拖动中"""
        if self._scaling and self._scale_start_pos:
            # 计算鼠标移动距离（斜向）
            current_pos = event.globalPosition().toPoint()
            delta = current_pos - self._scale_start_pos
            
            # 使用对角线距离来计算缩放变化
            # 向右下拖动增加，向左上拖动减少
            diagonal_delta = (delta.x() + delta.y()) / 2.0
            scale_change = diagonal_delta / 200.0  # 每200px改变1.0倍
            
            new_scale = self._scale_start_scale + scale_change
            new_scale = max(0.5, min(2.0, new_scale))  # 限制范围 0.5-2.0
            
            if abs(new_scale - self.content_scale) > 0.01:  # 避免过于频繁的更新
                self.content_scale = new_scale
                self._apply_content_scale()
                
            event.accept()
    
    def _on_scale_release(self, event):
        """结束缩放拖动"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._scaling = False
            self._scale_start_pos = None
            # 保存缩放比例
            self.settings.setValue("content_scale", self.content_scale)
            event.accept()
    
    def _apply_content_scale(self):
        """应用内容缩放比例"""
        # 更新所有内容的字体大小
        self._update_content()