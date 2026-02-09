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
from gui.widgets.item_detail_card_v2 import ItemDetailCard
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
        
        # ✅ 使用 Qt.WA_DontShowOnScreen - 这是最强的隐藏机制
        # 窗口会被创建但永远不会显示，直到我们手动移除这个属性
        self.setAttribute(Qt.WA_DontShowOnScreen, True)
        
        # ✅ 设置固定大小（从保存的设置中加载，或使用默认值）
        self.settings = QSettings("Reborn", "MonsterDetailWindow")
        saved_width = self.settings.value("window_width", 450, type=int)
        saved_height = self.settings.value("window_height", 650, type=int)
        
        # ✅ 立即设置大小（在显示之前）
        self.resize(saved_width, saved_height)
        
        # --- Focus Tracking ---
        self.last_focused_window = None
        # ----------------------

        self.current_monster = None
        self.current_item_id = None
        self.display_mode = 'monster'
        self.i18n = get_i18n()
        # track a single active item popup to avoid overlapping popups
        self._active_item_popup = None
        
        # ✅ 加载数据库
        self.items_db = self._load_items_db()
        self.skills_db = self._load_skills_db()
        
        # ✅ 内容缩放比例（默认1.0，范围0.5-2.0）
        self.content_scale = self.settings.value("content_scale", 1.0, type=float)
        self.content_scale = max(0.5, min(2.0, self.content_scale))  # 限制范围
        
        # ✅ 单例模式：预创建所有 ItemDetailCard 实例（只创建一次，复用）
        self._skill_cards_cache = {}  # {skill_id: ItemDetailCard}
        self._item_card_cache = None  # 物品详情卡片（单例）
        
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
        
        # ❌ 移除预创建（会导致启动时闪白框）
        # self._precreate_item_cards()
        
        # 🔥 新方案：创建一个虚拟卡片强制完成Qt首次渲染
        self._warmup_qt_rendering()
        
        # ✅ 初始化可调整大小的辅助工具
        self.frameless_helper = FramelessHelper(
            self,
            margin=5,           # 边缘检测区域
            snap_to_top=False,  # 不吸附顶部
            enable_drag=True,   # ✅ 启用拖拽
            enable_resize=True, # ✅ 启用调整大小
            debug=False
        )
        
        # 加载保存的窗口位置（但不加载大小，大小已经在开头设置了）
        pos = self.settings.value("pos")
        if pos:
            self.move(pos)
        
        # ✅ 创建缩放手柄（右下角）
        self._create_scale_handle()
        
        # ✅ 窗口已完全初始化，但仍然是 WA_DontShowOnScreen 状态
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
        # ✅ 设置空标题，避免显示"python"
        self.setWindowTitle("")
        
        # 独立的悬浮窗口
        self.setWindowFlags(
            Qt.WindowType.Tool |  # 工具窗口，不在任务栏显示
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)  # 显示时不激活焦点
        
        # ✅ 设置可调整大小的范围
        self.setMinimumSize(360, 400)
        self.setMaximumSize(800, 1200)
        # 大小已经在 __init__ 中设置

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
            # ✅ 正确策略：Preferred，让widget根据内容自适应
            from PySide6.QtWidgets import QSizePolicy
            self.content_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
            
            self.content_layout = QVBoxLayout(self.content_widget)
            self.content_layout.setSpacing(10)
            self.content_layout.setContentsMargins(0, 0, 0, 0)
            # ✅ 不设置对齐方式，让addStretch()控制空间分配
            
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
        
        # ✅ 如果窗口已经显示且是同一个怪物，不需要重新加载
        monster_id = getattr(monster, 'name_key', None) or getattr(monster, 'id', None)
        if self.isVisible() and hasattr(self, '_last_shown_monster_id') and self._last_shown_monster_id == monster_id:
            return
        
        self._last_shown_monster_id = monster_id
        
        # ✅ 先隐藏窗口
        was_visible = self.isVisible()
        if was_visible:
            self.hide()
        
        # ✅ 更新内容（窗口隐藏状态）
        self._update_content()
        
        # ✅ 恢复位置
        self._load_window_state()
        
        # ✅ 内容完全准备好后再显示
        self.show()
        self.raise_()

    def show_item_beside(self, anchor_widget, item_id):
        """
        显示物品详情在指定窗口旁边
        """
        self.display_mode = 'item'
        self.current_item_id = item_id
        
        # ✅ 如果窗口已经显示且是同一个物品，不需要重新加载
        if self.isVisible() and hasattr(self, '_last_shown_item_id') and self._last_shown_item_id == item_id:
            return
        
        self._last_shown_item_id = item_id
        
        # ✅ 先隐藏窗口
        was_visible = self.isVisible()
        if was_visible:
            self.hide()
        
        # ✅ 更新内容（窗口隐藏状态）
        self._update_content()
        
        # ✅ 定位并显示
        self._position_beside(anchor_widget)

    def show_beside(self, anchor_widget, monster):
        """
        显示在指定窗口旁边（自动选择左侧或右侧）
        ✅ 调整大小后仍保持紧贴sidebar
        """
        self.display_mode = 'monster'
        self.current_monster = monster
        
        # ✅ 如果窗口已经显示且是同一个怪物，不需要重新加载
        monster_id = getattr(monster, 'name_key', None) or getattr(monster, 'id', None)
        if self.isVisible() and hasattr(self, '_last_shown_monster_id') and self._last_shown_monster_id == monster_id:
            # 只需要重新定位（可能sidebar移动了）
            self._position_beside(anchor_widget)
            return
        
        self._last_shown_monster_id = monster_id
        
        # ✅ 先隐藏窗口，防止内容更新时的白框闪烁
        was_visible = self.isVisible()
        if was_visible:
            self.hide()
        
        # ✅ 更新内容（此时窗口隐藏，不会看到重建过程）
        self._update_content()
        
        # ✅ 内容准备完成后，定位并显示
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
        
        # ✅ 延迟显示：确保所有渲染完全结束后再显示
        # 增加延迟到50ms，给Qt更多时间完成布局
        from PySide6.QtCore import QTimer
        QTimer.singleShot(50, self._delayed_show)  # 延迟50ms显示

        # 停止隐藏定时器
        self.hide_timer.stop()
    
    def _delayed_show(self):
        """延迟显示窗口"""
        if not self.isVisible():
            # 🔥 双重保险：显示前再次确认窗口完全准备好
            self.repaint()  # 强制重绘
            self.show()
            self.raise_()
            self.activateWindow()

    def _update_content(self):
        """更新详情内容"""
        # ✅ 终极方案：完全隐藏窗口 + 移出屏幕
        was_visible = self.isVisible()
        old_pos = self.pos()  # 保存原位置
        
        # 1. 强制隐藏
        self.hide()
        self.setUpdatesEnabled(False)
        self.setAttribute(Qt.WA_DontShowOnScreen, True)
        
        # 2. 移动到屏幕外（负坐标）- 确保即使意外显示也看不到
        self.move(-10000, -10000)
        
        # 3. 阻止信号
        old_block_state = self.signalsBlocked()
        self.blockSignals(True)
        
        # 清空旧内容（只移除，不删除 widget）
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)  # 移除但不删除

        if self.display_mode == 'item' and self.current_item_id:
             scale = self.content_scale
             # ✅ 优化：首次创建时完全脱离父窗口，避免触发重绘
             if self._item_card_cache is None:
                 item_data = next((item for item in self.items_db if item.get("id") == self.current_item_id), {})
                 # 创建时不指定parent，完全独立
                 self._item_card_cache = ItemDetailCard(item_id=self.current_item_id, item_type="item",
                                            default_expanded=True, enable_tier_click=True, content_scale=scale,
                                            item_data=item_data, parent=None)
                 # 设置parent但延迟添加到布局
                 self._item_card_cache.setParent(self)
             else:
                 # ✅ 复用：只更新数据
                 item_data = next((item for item in self.items_db if item.get("id") == self.current_item_id), {})
                 self._item_card_cache.item_data = item_data
                 self._item_card_cache.item_id = self.current_item_id
             
             self.content_layout.addWidget(self._item_card_cache)
             
             
             # ✅ 恢复信号和渲染（针对物品模式提前返回）
             self.move(old_pos)
             self.blockSignals(old_block_state)
             self.setAttribute(Qt.WA_DontShowOnScreen, False)
             self.setUpdatesEnabled(True)
             if was_visible:
                 self.show()
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

            # ✅ 优化：首次创建时完全脱离父窗口
            for skill in m.skills:
                skill_id = skill.get("id", "")
                current_tier = skill.get("current_tier", "bronze").lower()
                
                # 检查缓存
                if skill_id not in self._skill_cards_cache:
                    # 首次创建：不指定parent，完全独立
                    skill_data = next((s for s in self.skills_db if s.get("id") == skill_id), {})
                    skill_card = ItemDetailCard(skill_id, item_type="skill", current_tier=current_tier, 
                                               default_expanded=True, enable_tier_click=True, content_scale=scale,
                                               item_data=skill_data, parent=None)
                    # 设置parent但延迟添加到布局
                    skill_card.setParent(self)
                    self._skill_cards_cache[skill_id] = skill_card
                else:
                    # ✅ 复用：从缓存获取
                    skill_card = self._skill_cards_cache[skill_id]
                
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
                
                
                def mousePressEvent(self, event):
                    """点击物品图标时，在怪物悬浮框下方展开显示该物品详情"""
                    if event.button() == Qt.LeftButton:
                        # 切换显示/隐藏物品详情
                        outer_self._toggle_item_detail(self.item_id, self.current_tier, self.content_scale, self.monster_item_data)
                    super().mousePressEvent(event)

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

        # ✅ 物品详情占位标记（点击掉落物品时会在这里插入ItemDetailCard）
        # 用一个变量标记当前展开的物品ID和对应的卡片widget
        if not hasattr(self, '_current_item_detail_card'):
            self._current_item_detail_card = None
            self._current_expanded_item_id = None

        # ✅ 关键修复：在底部添加弹性spacer，吸收多余空间
        # 这样卡片不会被拉伸，多余空间被spacer占用
        self.content_layout.addStretch(1)
        
        # ✅ 恢复窗口状态
        self.move(old_pos)  # 恢复原位置
        self.blockSignals(old_block_state)
        self.setAttribute(Qt.WA_DontShowOnScreen, False)
        self.setUpdatesEnabled(True)
        if was_visible:
            self.show()

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
        # ✅ 隐藏后重新设置 WA_DontShowOnScreen（下次显示时需要移除）
        self.setAttribute(Qt.WA_DontShowOnScreen, True)
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
    
    def _load_items_db(self):
        """加载物品数据库"""
        try:
            import json
            with open("assets/json/items_db.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"加载物品数据库失败: {e}")
            return []
    
    def _load_skills_db(self):
        """加载技能数据库"""
        try:
            import json
            with open("assets/json/skills_db.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"加载技能数据库失败: {e}")
            return []

    def _toggle_item_detail(self, item_id, current_tier, content_scale, monster_item_data):
        """
        切换物品详情展示
        如果点击的是同一个物品，则隐藏；如果是不同物品，则显示新物品详情
        在掉落物品行的下方直接插入 ItemDetailCard
        """
        # 如果点击的是当前已展开的物品，则移除卡片
        if self._current_expanded_item_id == item_id and self._current_item_detail_card:
            # 从布局中移除并删除卡片
            self.content_layout.removeWidget(self._current_item_detail_card)
            self._current_item_detail_card.deleteLater()
            self._current_item_detail_card = None
            self._current_expanded_item_id = None
            return
        
        # 如果已经有展开的卡片，先移除
        if self._current_item_detail_card:
            self.content_layout.removeWidget(self._current_item_detail_card)
            self._current_item_detail_card.deleteLater()
            self._current_item_detail_card = None
        
        # 记录新的展开物品ID
        self._current_expanded_item_id = item_id
        
        # 合并物品数据（从 items_db 加载完整数据，保留 monster 数据中的 enchantment）
        merged_item_data = None
        if monster_item_data:
            try:
                items_db_path = "assets/json/items_db.json"
                if os.path.exists(items_db_path):
                    with open(items_db_path, 'r', encoding='utf-8') as f:
                        items_db = json.load(f)
                        db_item = next((i for i in items_db if i.get('id') == item_id), None)
                        if db_item:
                            merged_item_data = db_item.copy()
                            if 'enchantment' in monster_item_data:
                                merged_item_data['enchantment'] = monster_item_data['enchantment']
            except Exception as e:
                print(f"[ItemDetail] Error merging item data: {e}")
        
        # 如果没有合并数据，直接从 items_db 加载
        if not merged_item_data:
            try:
                items_db_path = "assets/json/items_db.json"
                if os.path.exists(items_db_path):
                    with open(items_db_path, 'r', encoding='utf-8') as f:
                        items_db = json.load(f)
                        merged_item_data = next((i for i in items_db if i.get('id') == item_id), None)
            except Exception as e:
                print(f"[ItemDetail] Error loading item data: {e}")
        
        # 创建物品详情卡片
        if merged_item_data:
            item_card = ItemDetailCard(
                item_id=item_id,
                item_type='item',
                current_tier=current_tier,
                parent=self,
                default_expanded=True,
                enable_tier_click=True,
                content_scale=content_scale,
                item_data=merged_item_data
            )
            
            # 找到 addStretch 的位置（应该是最后一个item）
            stretch_index = self.content_layout.count() - 1
            
            # 在 stretch 之前插入卡片
            self.content_layout.insertWidget(stretch_index, item_card)
            self._current_item_detail_card = item_card
            
            # 自动滚动到卡片位置，确保新展开的内容可见
            QTimer.singleShot(100, lambda: self.scroll.ensureWidgetVisible(item_card))
        else:
            print(f"[ItemDetail] No data found for item: {item_id}")
    
    def _warmup_qt_rendering(self):
        """
        🔥 Qt渲染预热：在完全隐藏的状态下创建一个虚拟ItemDetailCard
        强制Qt完成所有首次渲染初始化，避免后续创建时的白框闪现
        """
        try:
            # 创建一个完整的虚拟数据结构，包含所有可能的字段
            dummy_data = {
                "id": "_warmup_",
                "starting_tier": "Bronze",
                "name": "Warmup",  # 使用简单字符串而不是dict
                "name_cn": "预热",
                "size": "medium / 中",
                "type": "equipment",
                "cooldown": "",
                "cooldown_tiers": "",
                "descriptions": [],
                "skills": [],
                "skills_passive": [],
                "quests": [],
                "enchantments": [],
                "hero": "Common / 通用"
            }
            
            # 使用关键字参数明确传递，避免参数顺序问题
            dummy_card = ItemDetailCard(
                item_id="_warmup_",
                item_type="skill",
                current_tier="bronze",
                parent=None,
                default_expanded=False,
                enable_tier_click=False,
                content_scale=1.0,
                item_data=dummy_data
            )
            
            # 立即销毁
            dummy_card.deleteLater()
            
            print("[DEBUG] Qt rendering warmup completed")
        except Exception as e:
            import traceback
            print(f"[WARNING] Qt rendering warmup failed: {e}")
            print(f"[WARNING] Traceback: {traceback.format_exc()}")