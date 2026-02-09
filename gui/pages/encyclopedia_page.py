"""
百科搜索页面 - 完全照抄React版本
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QScrollArea, QSplitter
)
from PySide6.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QIcon
from pathlib import Path
import json
from gui.widgets.item_detail_card_v2 import ItemDetailCard
from gui.widgets.flow_layout import FlowLayout


class EncyclopediaPage(QWidget):
    """百科搜索页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # ✅ 先加载配置（必须在使用config之前）
        self.config_path = Path("user_data/user_config.json")
        self.config = self._load_config()
        
        # 搜索状态
        self.search_query = {
            "keyword": "",
            "item_type": "all",  # all, item, skill
            "size": "",  # small, medium, large
            "start_tier": "",  # bronze, silver, gold, diamond, legendary
            "hero": "",  # Common, Pygmalien, Jules, Vanessa, Mak, Dooley, Stelle
        }
        self.selected_tags = []  # 普通标签（可多选）
        self.selected_hidden_tags = []  # 隐藏标签（可多选）
        
        # ✅ 从配置文件加载match_mode
        self.match_mode = self.config.get("match_mode", "all")  # all 或 any
        
        self.is_filter_collapsed = False  # 过滤器收起状态
        self.filter_expanded_height = 0  # 记录展开时的高度
        
        # 搜索结果
        self.search_results = []
        self.is_searching = False
        
        # 记住上次物品尺寸（用于类型切换）
        self.last_item_size = ""
        
        # ✅ 懒加载相关
        self.displayed_count = 0  # 当前显示的卡片数量
        self.batch_size = 50  # ✅ 每批加载50个（原20）
        
        # 初始化按钮字典
        self.type_buttons = {}
        self.size_buttons = {}
        self.tier_buttons = {}
        self.hero_buttons = {}
        self.tag_buttons = {}
        self.hidden_tag_buttons = {}
        
        # 加载数据
        self.items_db = self._load_items_db()
        self.skills_db = self._load_skills_db()
        
        # 防抖定时器
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)
        
        self._init_ui()
        
        # 恢复splitter位置
        self._restore_splitter_state()
        
        # 初始化时执行一次搜索
        self._perform_search()
    
    def _load_config(self) -> dict:
        """加载配置"""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_config(self):
        """保存配置"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _load_items_db(self) -> list:
        """加载物品数据库"""
        items_db_path = Path(__file__).parent.parent.parent / "assets" / "json" / "items_db.json"
        try:
            with open(items_db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载物品数据库失败: {e}")
            return []
    
    def _load_skills_db(self) -> list:
        """加载技能数据库"""
        skills_db_path = Path(__file__).parent.parent.parent / "assets" / "json" / "skills_db.json"
        try:
            with open(skills_db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载技能数据库失败: {e}")
            return []
    
    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ✅ 搜索过滤器区域 - 使用QSplitter实现上下可拖拽调整
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.setHandleWidth(10)  # ✅ 增大到10px，方便点击
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background: rgba(255, 205, 25, 0.3);
                margin: 2px 0;
            }
            QSplitter::handle:hover {
                background: rgba(255, 205, 25, 0.6);
            }
        """)
        # 监听splitter移动，保存位置
        self.splitter.splitterMoved.connect(self._on_splitter_moved)
        
        # 上半部分：搜索过滤器区域
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)
        
        self.filter_container = self._create_filter_container()
        top_layout.addWidget(self.filter_container)
        
        self.stats_bar = self._create_stats_bar()
        top_layout.addWidget(self.stats_bar)
        
        self.splitter.addWidget(top_widget)
        
        # 下半部分：滚动区域 - 显示搜索结果
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 204, 0, 0.3);
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 204, 0, 0.5);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)
        
        # ✅ 连接滚动事件，实现懒加载
        scroll_area.verticalScrollBar().valueChanged.connect(self._on_scroll)
        
        # ✅ 创建一个堆叠容器，用于放置结果和加载蒙版
        stacked_container = QWidget()
        stacked_layout = QVBoxLayout(stacked_container)
        stacked_layout.setContentsMargins(0, 0, 0, 0)
        stacked_layout.setSpacing(0)
        
        # 结果容器
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(15, 15, 15, 15)
        self.results_layout.setSpacing(8)
        # ✅ 关键修复：设置顶部对齐，防止少数卡片被拉伸填满整个空间
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        stacked_layout.addWidget(self.results_container)
        
        # ✅ 创建加载蒙版（覆盖在结果上方）
        self.loading_overlay = QWidget(stacked_container)
        self.loading_overlay.setStyleSheet("""
            QWidget {
                background: rgba(30, 30, 30, 0.85);
            }
        """)
        self.loading_overlay.hide()
        
        overlay_layout = QVBoxLayout(self.loading_overlay)
        overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 加载动画标签 - 使用更醒目的样式
        self.loading_label = QLabel("⟳ 加载中...")
        self.loading_label.setStyleSheet("""
            QLabel {
                color: #ffcc00;
                font-size: 24px;
                font-weight: bold;
                font-family: 'Microsoft YaHei UI';
                background: transparent;
                padding: 20px;
            }
        """)
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay_layout.addWidget(self.loading_label)
        
        # ✅ 创建旋转动画
        from PySide6.QtCore import QTimer
        self.loading_timer = QTimer()
        self.loading_timer.timeout.connect(self._update_loading_animation)
        self.loading_rotation = 0
        
        # ✅ 监听容器大小变化，调整蒙版大小
        stacked_container.resizeEvent = lambda event: self._on_container_resized(event, stacked_container)
        
        scroll_area.setWidget(stacked_container)
        self.splitter.addWidget(scroll_area)
        
        # 设置初始比例 (过滤器:结果 = 2:3)
        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 3)
        
        main_layout.addWidget(self.splitter)
    
    def _create_filter_container(self) -> QWidget:
        """创建搜索过滤器容器"""
        container = QWidget()
        container.setObjectName("filterContainer")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # ✅ 标题行（显示标题、类型切换按钮（居中）、收起按钮）
        header_widget = QWidget()
        header_widget.setFixedHeight(48)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(8)
        
        # 左侧：标题
        title_label = QLabel("搜索过滤器")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #ffcd19;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # ✅ 中间：物品/技能过滤按钮（水平居中）- 必须选中一个
        self.type_buttons = {}
        for type_val, label in [("item", "物品"), ("skill", "技能")]:
            btn = self._create_toggle_button(label, active=(type_val == "item"))  # 默认选中物品
            btn.clicked.connect(lambda checked, t=type_val: self._set_item_type(t))
            header_layout.addWidget(btn)
            self.type_buttons[type_val] = btn
        
        header_layout.addStretch()
        
        # 右侧：收起按钮（仅触发动画，不隐藏内容）
        self.collapse_btn = QPushButton("收起 ▲")
        self.collapse_btn.setFixedSize(80, 28)
        self.collapse_btn.clicked.connect(self._trigger_collapse_animation)
        self.collapse_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid rgba(255, 205, 25, 0.3);
                color: #ffcd19;
                border-radius: 4px;
                font-size: 11px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background: rgba(255, 205, 25, 0.1);
                border-color: rgba(255, 205, 25, 0.5);
            }
        """)
        header_layout.addWidget(self.collapse_btn)
        
        container_layout.addWidget(header_widget)
        
        # ✅ 过滤器内容（可折叠，可滚动）
        self.filter_scroll = QScrollArea()
        self.filter_scroll.setWidgetResizable(True)
        self.filter_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.filter_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 204, 0, 0.3);
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 204, 0, 0.5);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)
        
        self.filter_content = QWidget()
        filter_content_layout = QVBoxLayout(self.filter_content)
        filter_content_layout.setContentsMargins(12, 12, 12, 12)
        filter_content_layout.setSpacing(12)
        
        # 第1行：关键词搜索
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("搜索名称 / 描述...")
        self.keyword_input.textChanged.connect(self._on_keyword_changed)
        self.keyword_input.setStyleSheet("""
            QLineEdit {
                font-family: 'Microsoft YaHei UI';
                background: #1A1714;
                border: 1px solid #3d352f;
                color: #eee;
                padding: 10px 14px;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #ffcc00;
                background: #1A1714;
            }
            QLineEdit::placeholder {
                color: #666;
            }
        """)
        filter_content_layout.addWidget(self.keyword_input)
        
        # ✅ 匹配模式按钮组（无副标题）
        match_mode_container = QWidget()
        match_mode_layout = FlowLayout(match_mode_container, h_spacing=6, v_spacing=6)
        
        # ✅ 根据配置文件初始化按钮状态
        self.btn_match_all = self._create_toggle_button("匹配所有", active=(self.match_mode == "all"))
        self.btn_match_all.clicked.connect(lambda: self._set_match_mode("all"))
        match_mode_layout.addWidget(self.btn_match_all)
        
        self.btn_match_any = self._create_toggle_button("匹配任一", active=(self.match_mode == "any"))
        self.btn_match_any.clicked.connect(lambda: self._set_match_mode("any"))
        match_mode_layout.addWidget(self.btn_match_any)
        
        filter_content_layout.addWidget(match_mode_container)
        
        # 第2行：尺寸（去掉类型，因为已经移到顶部）
        self.size_title = QLabel("尺寸")
        self.size_title.setStyleSheet("font-size: 11px; color: #888; font-weight: bold;")
        filter_content_layout.addWidget(self.size_title)
        
        # 尺寸按钮组（只在选择物品时显示）
        self.size_group_widget = QWidget()
        size_layout = FlowLayout(self.size_group_widget, h_spacing=6, v_spacing=6)
        
        self.size_buttons = {}
        for size_val, label in [("small", "小"), ("medium", "中"), ("large", "大")]:
            btn = self._create_toggle_button(label)
            btn.clicked.connect(lambda checked, s=size_val: self._set_size(s))
            size_layout.addWidget(btn)
            self.size_buttons[size_val] = btn
        
        filter_content_layout.addWidget(self.size_group_widget)
        
        # 第3行：品级
        tier_title = QLabel("品级")
        tier_title.setStyleSheet("font-size: 11px; color: #888; font-weight: bold;")
        filter_content_layout.addWidget(tier_title)
        
        tier_container = QWidget()
        tier_layout = FlowLayout(tier_container, h_spacing=6, v_spacing=6)
        
        self.tier_buttons = {}
        for tier_val, label, color in [
            ("bronze", "青铜", "#cd7f32"),
            ("silver", "白银", "#c0c0c0"),
            ("gold", "黄金", "#ffd700"),
            ("diamond", "钻石", "#b9f2ff"),
            ("legendary", "传说", "#ff4500")
        ]:
            btn = self._create_toggle_button(label, color=color)
            btn.clicked.connect(lambda checked, t=tier_val: self._set_tier(t))
            tier_layout.addWidget(btn)
            self.tier_buttons[tier_val] = btn
        
        filter_content_layout.addWidget(tier_container)
        
        # 第4行：英雄选择
        hero_title = QLabel("英雄")
        hero_title.setStyleSheet("font-size: 11px; color: #888; font-weight: bold;")
        filter_content_layout.addWidget(hero_title)
        
        hero_container = QWidget()
        # ✅ 减小垂直间距，确保按钮在同一基线
        hero_layout = FlowLayout(hero_container, h_spacing=6, v_spacing=4)
        
        self.hero_buttons = {}
        for hero_val, label, avatar in [
            ("Common", "通用", ""),
            ("Pygmalien", "猪", "images/heroes/pygmalien.webp"),
            ("Jules", "朱尔斯", "images/heroes/jules.webp"),
            ("Vanessa", "瓦内莎", "images/heroes/vanessa.webp"),
            ("Mak", "马克", "images/heroes/mak.webp"),
            ("Dooley", "多利", "images/heroes/dooley.webp"),
            ("Stelle", "斯黛尔", "images/heroes/stelle.webp")
        ]:
            btn = self._create_hero_button(label, avatar, hero_val)
            btn.clicked.connect(lambda checked, h=hero_val: self._set_hero(h))
            hero_layout.addWidget(btn)
            self.hero_buttons[hero_val] = btn
        
        filter_content_layout.addWidget(hero_container)
        
        # ✅ 第5行：标签（可多选）- 使用FlowLayout自动换行
        tag_title = QLabel("标签 (可多选)")
        tag_title.setStyleSheet("font-size: 11px; color: #888; font-weight: bold;")
        filter_content_layout.addWidget(tag_title)
        
        # 标签列表（按中文排序）
        tags = [
            ["Drone", "无人机"], 
            ["Property", "地产"], 
            ["Ray", "射线"], 
            ["Tool", "工具"], 
            ["Dinosaur", "恐龙"], 
            ["Loot", "战利品"], 
            ["Apparel", "服饰"], 
            ["Core", "核心"], 
            ["Weapon", "武器"], 
            ["Aquatic", "水系"], 
            ["Toy", "玩具"], 
            ["Tech", "科技"], 
            ["Potion", "药水"], 
            ["Reagent", "原料"], 
            ["Vehicle", "载具"], 
            ["Relic", "遗物"], 
            ["Food", "食物"], 
            ["Dragon", "龙"],
            ["Friend", "伙伴"]
        ]
        tags.sort(key=lambda x: x[1])
        
        # 使用FlowLayout自动换行
        tag_container = QWidget()
        tag_layout = FlowLayout(tag_container, h_spacing=6, v_spacing=6)
        
        for val, label in tags:
            btn = self._create_toggle_button(label)
            btn.setProperty("tag_val", val)
            btn.clicked.connect(lambda checked, v=val: self._toggle_tag(v))
            tag_layout.addWidget(btn)
            self.tag_buttons[val] = btn
        
        filter_content_layout.addWidget(tag_container)
        
        # 第6行：隐藏标签（可多选）
        hidden_tag_title = QLabel("隐藏标签 (可多选)")
        hidden_tag_title.setStyleSheet("font-size: 11px; color: #888; font-weight: bold;")
        filter_content_layout.addWidget(hidden_tag_title)
        
        # 隐藏标签分组（带图标和颜色）
        hidden_tag_groups = [
            {"tags": [["Ammo", "弹药"], ["AmmoRef", "弹药相关"]], "color": "#ffc107", "icon": "Ammo.webp"},
            {"tags": [["Burn", "灼烧"], ["BurnRef", "灼烧相关"]], "color": "#ff9f45", "icon": "Burn.webp"},
            {"tags": [["Charge", "充能"]], "color": "#2196F3", "icon": "Charge.webp"},
            {"tags": [["Cooldown", "冷却"], ["CooldownReference", "冷却相关"]], "color": "#00bcd4", "icon": "Cooldown.webp"},
            {"tags": [["Crit", "暴击"], ["CritRef", "暴击相关"]], "color": "#f5503d", "icon": "CritChance.webp"},
            {"tags": [["Damage", "伤害"], ["DamageRef", "伤害相关"]], "color": "#f5503d", "icon": "Damage.webp"},
            {"tags": [["EconomyRef", "经济相关"], ["Gold", "金币"]], "color": "#ffcd19", "icon": "Income.webp"},
            {"tags": [["Flying", "飞行"], ["FlyingRef", "飞行相关"]], "color": "#64b5f6", "icon": "Flying.webp"},
            {"tags": [["Freeze", "冻结"], ["FreezeRef", "冻结相关"]], "color": "#22b8cf", "icon": "Freeze.webp"},
            {"tags": [["Haste", "加速"], ["HasteRef", "加速相关"]], "color": "#00ecc3", "icon": "Haste.webp"},
            {"tags": [["Heal", "治疗"], ["HealRef", "治疗相关"]], "color": "#8eea31", "icon": "Health.webp"},
            {"tags": [["Health", "生命值"], ["HealthRef", "生命值相关"]], "color": "#8eea31", "icon": "MaxHPHeart.webp"},
            {"tags": [["Lifesteal", "生命偷取"]], "color": "#e91e63", "icon": "Lifesteal.webp"},
            {"tags": [["Poison", "剧毒"], ["PoisonRef", "剧毒相关"]], "color": "#0ebe4f", "icon": "Poison.webp"},
            {"tags": [["Quest", "任务"]], "color": "#9098fe", "icon": "Joy.webp"},
            {"tags": [["Regen", "再生"], ["RegenRef", "再生相关"]], "color": "#4caf50", "icon": "Regen.webp"},
            {"tags": [["Shield", "护盾"], ["ShieldRef", "护盾相关"]], "color": "#f4cf20", "icon": "Shield.webp"},
            {"tags": [["Slow", "减速"], ["SlowRef", "减速相关"]], "color": "#5c7cfa", "icon": "Slowness.webp"},
        ]
        
        hidden_tag_container = QWidget()
        hidden_tag_layout = FlowLayout(hidden_tag_container, h_spacing=6, v_spacing=6)
        
        self.hidden_tag_buttons = {}
        for group in hidden_tag_groups:
            for tag_val, label in group["tags"]:
                btn = self._create_toggle_button(label, color=group["color"], icon=group.get("icon"))
                btn.setProperty("tag_val", tag_val)
                btn.clicked.connect(lambda checked, v=tag_val: self._toggle_hidden_tag(v))
                hidden_tag_layout.addWidget(btn)
                self.hidden_tag_buttons[tag_val] = btn
        
        filter_content_layout.addWidget(hidden_tag_container)
        
        # ✅ 在所有内容后添加弹性空间，防止上面的组件被拉伸
        filter_content_layout.addStretch()
        
        # 将filter_content放入滚动区域
        self.filter_scroll.setWidget(self.filter_content)
        container_layout.addWidget(self.filter_scroll)
        
        # 容器样式
        container.setStyleSheet("""
            #filterContainer {
                background: #2b2621;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        
        return container
    
    def _create_toggle_button(self, text: str, active: bool = False, color: str = None, icon: str = None) -> QPushButton:
        """创建切换按钮 - ✅ 支持webp图标 + 最小宽度"""
        btn = QPushButton()
        btn.setCheckable(False)  # 不使用 QCheckBox，手动管理状态
        btn.setProperty("active", active)
        
        # ✅ 如果有图标，加载webp图片
        if icon:
            icon_path = Path(__file__).parent.parent.parent / "assets" / "images" / "GUI" / icon
            if icon_path.exists():
                pixmap = QPixmap(str(icon_path))
                if not pixmap.isNull():
                    # 缩放图标到16x16
                    scaled_pixmap = pixmap.scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, 
                                                  Qt.TransformationMode.SmoothTransformation)
                    btn.setIcon(QIcon(scaled_pixmap))
                    btn.setIconSize(QSize(16, 16))
        
        btn.setText(text)
        
        style = """
            QPushButton {
                background: rgba(0, 0, 0, 0.2);
                color: #a0937d;
                border: 1px solid #7d6b4a;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 13px;
                text-align: left;
            }
            QPushButton:hover {
                border-color: #d4af37;
                color: #fff;
            }
            QPushButton[active="true"] {
                background: rgba(255, 204, 0, 0.1);
                border-color: #ffcc00;
                color: #ffcc00;
                font-weight: bold;
            }
        """
        
        if color:
            style += f"""
                QPushButton {{
                    color: {color};
                }}
                QPushButton[active="true"] {{
                    color: {color};
                }}
            """
        
        btn.setStyleSheet(style)
        return btn
    
    def _create_hero_button(self, label: str, avatar_path: str, hero_val: str) -> QPushButton:
        """创建英雄按钮（带头像）- 完全按照React CSS"""
        btn = QPushButton()
        btn.setProperty("active", False)
        btn.setProperty("hero_val", hero_val)
        btn.setToolTip(label)
        
        if avatar_path:
            # 加载头像
            full_path = Path(__file__).parent.parent.parent / "assets" / avatar_path
            if full_path.exists():
                pixmap = QPixmap(str(full_path))
                # ✅ 完全按照CSS：按钮42x42，图片36x36
                btn.setFixedSize(42, 42)
                btn.setIconSize(QSize(36, 36))
                btn.setIcon(pixmap)
            else:
                btn.setFixedSize(42, 42)
            
            # ✅ CSS样式完全复刻
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(0, 0, 0, 0.2);
                    border: 2px solid #7d6b4a;
                    border-radius: 21px;
                    padding: 3px;
                }
                QPushButton:hover {
                    border-color: #d4af37;
                }
                QPushButton[active="true"] {
                    border-color: #ffcc00;
                }
            """)
        else:
            # ✅ 通用按钮：高度改为32px，与品级按钮一致
            btn.setText(label)
            btn.setFixedHeight(32)  # 只固定高度，宽度自适应文字
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(0, 0, 0, 0.2);
                    color: #a0937d;
                    border: 1px solid #7d6b4a;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    border-color: #d4af37;
                    color: #fff;
                }
                QPushButton[active="true"] {
                    background: rgba(255, 204, 0, 0.1);
                    border-color: #ffcc00;
                    color: #ffcc00;
                    font-weight: bold;
                }
            """)
        
        return btn
    
    def _create_stats_bar(self) -> QWidget:
        """创建结果统计栏"""
        bar = QWidget()
        bar.setFixedHeight(40)
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(12, 8, 12, 8)
        bar_layout.setSpacing(12)
        
        # 结果统计
        self.stats_label = QLabel("找到 <b>0</b> 个结果")
        self.stats_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #a0937d;
            }
        """)
        bar_layout.addWidget(self.stats_label)
        bar_layout.addStretch()
        
        # 清空筛选按钮
        clear_btn = QPushButton("清空筛选")
        clear_btn.setFixedSize(80, 28)
        clear_btn.clicked.connect(self._clear_filters)
        clear_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 69, 58, 0.15);
                border: 1px solid rgba(255, 69, 58, 0.4);
                color: #ff6666;
                border-radius: 4px;
                font-size: 11px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background: rgba(255, 69, 58, 0.25);
                border-color: rgba(255, 69, 58, 0.6);
            }
        """)
        bar_layout.addWidget(clear_btn)
        
        bar.setStyleSheet("""
            QWidget {
                background: rgba(0, 0, 0, 0.2);
                border-top: 1px solid rgba(255, 255, 255, 0.05);
            }
        """)
        
        return bar
    
    def _trigger_collapse_animation(self):
        """触发收起/展开动画（不隐藏内容）"""
        self.is_filter_collapsed = not self.is_filter_collapsed
        
        # 获取当前splitter的大小
        current_sizes = self.splitter.sizes()
        total_height = sum(current_sizes)
        
        if self.is_filter_collapsed:
            # 收起：记录当前高度，隐藏过滤内容和统计栏
            self.filter_expanded_height = current_sizes[0]
            target_height = 48  # 只显示标题栏48px
            self.collapse_btn.setText("展开 ▼")
            # 隐藏过滤内容和统计栏
            self.filter_scroll.hide()
            self.stats_bar.hide()
            # 隐藏splitter拖动手柄
            self.splitter.handle(1).hide()
        else:
            # 展开：恢复到之前的高度，显示过滤内容和统计栏
            target_height = self.filter_expanded_height if self.filter_expanded_height > 0 else int(total_height * 0.4)
            self.collapse_btn.setText("收起 ▲")
            self.filter_scroll.show()
            self.stats_bar.show()
            # 显示splitter拖动手柄
            self.splitter.handle(1).show()
        
        # 计算目标sizes
        target_sizes = [target_height, total_height - target_height]
        
        # 创建动画
        if hasattr(self, '_collapse_animation') and self._collapse_animation.state() == QPropertyAnimation.State.Running:
            self._collapse_animation.stop()
        
        # 使用QVariantAnimation动画splitter的sizes
        self._animate_splitter(current_sizes, target_sizes)
    
    def _animate_splitter(self, start_sizes, end_sizes):
        """动画调整splitter大小"""
        from PySide6.QtCore import QVariantAnimation
        
        animation = QVariantAnimation()
        animation.setDuration(300)  # 300ms动画
        animation.setStartValue(start_sizes[0])
        animation.setEndValue(end_sizes[0])
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        total = sum(start_sizes)
        
        def update_sizes(value):
            # 动态更新splitter的sizes
            new_sizes = [int(value), total - int(value)]
            self.splitter.setSizes(new_sizes)
        
        animation.valueChanged.connect(update_sizes)
        animation.start()
        
        # 保存引用防止被垃圾回收
        self._collapse_animation = animation
    
    def _set_match_mode(self, mode: str):
        """设置匹配模式"""
        self.match_mode = mode
        # ✅ 保存到配置文件
        self.config["match_mode"] = mode
        self._save_config()
        
        self.btn_match_all.setProperty("active", mode == "all")
        self.btn_match_all.style().unpolish(self.btn_match_all)
        self.btn_match_all.style().polish(self.btn_match_all)
        
        self.btn_match_any.setProperty("active", mode == "any")
        self.btn_match_any.style().unpolish(self.btn_match_any)
        self.btn_match_any.style().polish(self.btn_match_any)
        
        self._debounced_search()
    
    def _set_item_type(self, type_val: str):
        """设置物品类型 - 必须选中一个"""
        # ✅ 不允许取消选择，必须选中一个
        if self.search_query["item_type"] == type_val:
            return  # 已经选中，不做任何操作
        
        # 切换类型
        old_type = self.search_query["item_type"]
        self.search_query["item_type"] = type_val
        
        if type_val == "skill":
            # 切换到技能：隐藏尺寸筛选（包括标题和按钮）
            self.last_item_size = self.search_query["size"]
            self.search_query["size"] = ""
            self.size_title.hide()
            self.size_group_widget.hide()
        else:
            # 切换到物品：显示尺寸筛选
            if old_type == "skill" and self.last_item_size:
                self.search_query["size"] = self.last_item_size
            self.size_title.show()
            self.size_group_widget.show()
        
        # 更新按钮状态
        for t, btn in self.type_buttons.items():
            btn.setProperty("active", t == self.search_query["item_type"])
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
        # 更新尺寸按钮状态
        self._update_size_buttons()
        
        self._debounced_search()
    
    def _set_size(self, size_val: str):
        """设置尺寸"""
        if self.search_query["size"] == size_val:
            self.search_query["size"] = ""
        else:
            self.search_query["size"] = size_val
        
        self._update_size_buttons()
        self._debounced_search()
    
    def _update_size_buttons(self):
        """更新尺寸按钮状态"""
        for s, btn in self.size_buttons.items():
            btn.setProperty("active", s == self.search_query["size"])
            btn.style().unpolish(btn)
            btn.style().polish(btn)
    
    def _set_tier(self, tier_val: str):
        """设置品级"""
        if self.search_query["start_tier"] == tier_val:
            self.search_query["start_tier"] = ""
        else:
            self.search_query["start_tier"] = tier_val
        
        for t, btn in self.tier_buttons.items():
            btn.setProperty("active", t == self.search_query["start_tier"])
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
        self._debounced_search()
    
    def _set_hero(self, hero_val: str):
        """设置英雄"""
        if self.search_query["hero"] == hero_val:
            self.search_query["hero"] = ""
        else:
            self.search_query["hero"] = hero_val
        
        for h, btn in self.hero_buttons.items():
            btn.setProperty("active", h == self.search_query["hero"])
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
        self._debounced_search()
    
    def _toggle_tag(self, tag_val: str):
        """切换普通标签选中状态"""
        if tag_val in self.selected_tags:
            self.selected_tags.remove(tag_val)
        else:
            self.selected_tags.append(tag_val)
        
        # 更新按钮状态
        btn = self.tag_buttons.get(tag_val)
        if btn:
            btn.setProperty("active", tag_val in self.selected_tags)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
        self._debounced_search()
    
    def _toggle_hidden_tag(self, tag_val: str):
        """切换隐藏标签选中状态"""
        if tag_val in self.selected_hidden_tags:
            self.selected_hidden_tags.remove(tag_val)
        else:
            self.selected_hidden_tags.append(tag_val)
        
        # 更新按钮状态
        btn = self.hidden_tag_buttons.get(tag_val)
        if btn:
            btn.setProperty("active", tag_val in self.selected_hidden_tags)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
        self._debounced_search()
    
    def _on_keyword_changed(self, text: str):
        """关键词改变回调"""
        self.search_query["keyword"] = text
        self._debounced_search()
    
    def _debounced_search(self):
        """防抖搜索 - 300ms延迟"""
        self.search_timer.stop()
        self.search_timer.start(300)
    
    def _clear_filters(self):
        """清空所有筛选条件"""
        self.search_query = {
            "keyword": "",
            "item_type": "item",  # ✅ 重置为默认选中物品
            "size": "",
            "start_tier": "",
            "hero": "",
        }
        self.selected_tags = []
        self.selected_hidden_tags = []
        self.match_mode = "all"
        
        # 重置UI
        self.keyword_input.clear()
        
        # ✅ 显示尺寸筛选（因为默认是物品）
        self.size_title.show()
        self.size_group_widget.show()
        
        # 重置按钮状态
        for t, btn in self.type_buttons.items():
            btn.setProperty("active", t == "item")  # 默认选中物品
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
        for btn in self.size_buttons.values():
            btn.setProperty("active", False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
        for btn in self.tier_buttons.values():
            btn.setProperty("active", False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
        for btn in self.hero_buttons.values():
            btn.setProperty("active", False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
        # ✅ 重置标签按钮
        for btn in self.tag_buttons.values():
            btn.setProperty("active", False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
        for btn in self.hidden_tag_buttons.values():
            btn.setProperty("active", False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
        self.size_group_widget.setVisible(True)
        # ✅ 不重置match_mode，保持用户上次的选择
        # self._set_match_mode("all")
        self._perform_search()
    
    def _perform_search(self):
        """执行搜索"""
        self.is_searching = True
        self.stats_label.setText("🔍 搜索中...")
        
        # ✅ 根据类型选择数据源
        if self.search_query["item_type"] == "skill":
            source_db = self.skills_db
        else:
            source_db = self.items_db
        
        # 过滤逻辑
        results = []
        for item in source_db:
            if self._match_item(item):
                results.append(item)
        
        self.search_results = results
        self.is_searching = False
        
        # 更新统计
        self.stats_label.setText(f'找到 <b style="color: #ffcc00;">{len(results)}</b> 个结果')
        
        # 更新结果显示
        self._update_results_display()
    
    def _match_item(self, item: dict) -> bool:
        """判断物品是否匹配搜索条件"""
        # ✅ 技能数据结构不同，需要特殊处理
        is_skill = self.search_query["item_type"] == "skill"
        
        # ✅ 过滤掉 name_cn 为空的技能
        if is_skill:
            name_cn = item.get("name_cn", "").strip()
            if not name_cn:
                return False
        
        # 关键词匹配
        if self.search_query["keyword"]:
            keyword = self.search_query["keyword"].lower()
            
            # ✅ 优先匹配名称
            if is_skill:
                name_match = (keyword in item.get("name_en", "").lower() or 
                            keyword in item.get("name_cn", "").lower())
            else:
                name_match = (keyword in item.get("name", "").lower() or 
                            keyword in item.get("name_cn", "").lower())
            
            # 如果名称匹配，直接返回（优先级最高）
            if name_match:
                pass  # 继续后续检查
            else:
                # ✅ 名称不匹配时，模糊搜索所有字段
                content_match = False
                
                if is_skill:
                    # 技能：搜索 description, descriptions 数组
                    if keyword in item.get("description_en", "").lower():
                        content_match = True
                    elif keyword in item.get("description_cn", "").lower():
                        content_match = True
                    else:
                        # 搜索 descriptions 数组
                        descriptions = item.get("descriptions", [])
                        for desc in descriptions:
                            if isinstance(desc, dict):
                                if keyword in desc.get("en", "").lower() or keyword in desc.get("cn", "").lower():
                                    content_match = True
                                    break
                else:
                    # 物品：搜索 skills, skills_passive 等所有文本字段
                    # 1. 搜索 skills 数组
                    skills = item.get("skills", [])
                    for skill in skills:
                        if isinstance(skill, dict):
                            if keyword in skill.get("en", "").lower() or keyword in skill.get("cn", "").lower():
                                content_match = True
                                break
                        elif isinstance(skill, str) and keyword in skill.lower():
                            content_match = True
                            break
                    
                    # 2. 搜索 skills_passive 数组
                    if not content_match:
                        skills_passive = item.get("skills_passive", [])
                        for skill in skills_passive:
                            if isinstance(skill, dict):
                                if keyword in skill.get("en", "").lower() or keyword in skill.get("cn", "").lower():
                                    content_match = True
                                    break
                            elif isinstance(skill, str) and keyword in skill.lower():
                                content_match = True
                                break
                    
                    # 3. 搜索 enchantments 数组
                    if not content_match:
                        enchantments = item.get("enchantments", [])
                        for ench in enchantments:
                            if isinstance(ench, dict):
                                if keyword in ench.get("en", "").lower() or keyword in ench.get("cn", "").lower():
                                    content_match = True
                                    break
                    
                    # 4. 搜索 quests 数组
                    if not content_match:
                        quests = item.get("quests", [])
                        for quest in quests:
                            if isinstance(quest, dict):
                                target_en = quest.get("en_target", "")
                                target_cn = quest.get("cn_target", "")
                                reward_en = quest.get("en_reward", "")
                                reward_cn = quest.get("cn_reward", "")
                                if (keyword in target_en.lower() or keyword in target_cn.lower() or
                                    keyword in reward_en.lower() or keyword in reward_cn.lower()):
                                    content_match = True
                                    break
                
                # 如果名称和内容都不匹配，返回 False
                if not content_match:
                    return False
        
        # ✅ 技能不需要类型和尺寸匹配（已经通过数据源筛选）
        if not is_skill:
            # 类型匹配（仅物品）
            if self.search_query["item_type"] != "all":
                item_type = item.get("type", "").lower()
                if self.search_query["item_type"] == "skill" and item_type != "skill":
                    return False
                elif self.search_query["item_type"] == "item" and item_type == "skill":
                    return False
            
            # 尺寸匹配（仅物品）
            if self.search_query["size"]:
                size = item.get("size", "").split(" / ")[0].lower()
                if size != self.search_query["size"]:
                    return False
        
        # ✅ 品级匹配 - 使用starting_tier字段
        if self.search_query["start_tier"]:
            starting_tier_raw = item.get("starting_tier", "")
            if starting_tier_raw:
                # 解析 "Bronze / 青铜" 格式
                tier = starting_tier_raw.split(" / ")[0].lower()
                if tier != self.search_query["start_tier"]:
                    return False
            else:
                return False
        
        # 英雄匹配
        if self.search_query["hero"]:
            heroes_raw = item.get("heroes", "")
            
            # ✅ 解析英雄字符串："Vanessa / 凡妮莎 | Mak / 马克" → ["Vanessa", "Mak"]
            hero_keys = []
            if isinstance(heroes_raw, str) and heroes_raw:
                # 分割 | 获取各个英雄
                hero_parts = [h.strip() for h in heroes_raw.split("|")]
                for hero_part in hero_parts:
                    # 提取英文部分 "Vanessa / 凡妮莎" -> "Vanessa"
                    if " / " in hero_part:
                        hero_key = hero_part.split(" / ")[0].strip()
                        hero_keys.append(hero_key)
                    else:
                        hero_keys.append(hero_part.strip())
            elif isinstance(heroes_raw, list):
                # 如果是数组格式
                for hero in heroes_raw:
                    hero_key = hero.split(" / ")[0].strip() if isinstance(hero, str) else str(hero)
                    hero_keys.append(hero_key)
            
            # 检查选中的英雄是否在列表中
            if self.search_query["hero"] not in hero_keys:
                return False
        
        # ✅ 标签匹配（普通标签） - 正确解析 "Weapon / 武器 | Friend / 伙伴" 格式
        if self.selected_tags:
            item_tags_raw = item.get("tags", "")
            # 解析标签字符串
            item_tag_keys = []
            if isinstance(item_tags_raw, str) and item_tags_raw:
                # 分割 | 获取各个标签
                tag_parts = [t.strip() for t in item_tags_raw.split("|")]
                for tag_part in tag_parts:
                    # 提取英文部分 "Weapon / 武器" -> "Weapon"
                    if " / " in tag_part:
                        tag_key = tag_part.split(" / ")[0].strip()
                        item_tag_keys.append(tag_key)
                    else:
                        item_tag_keys.append(tag_part.strip())
            
            if self.match_mode == "all":
                # 所有选中的标签都必须在物品标签中
                for tag in self.selected_tags:
                    if tag not in item_tag_keys:
                        return False
            else:  # any
                # 至少有一个选中的标签在物品标签中
                has_any = False
                for tag in self.selected_tags:
                    if tag in item_tag_keys:
                        has_any = True
                        break
                if not has_any:
                    return False
        
        # ✅ 隐藏标签匹配 - 正确解析字符串格式
        if self.selected_hidden_tags:
            item_hidden_tags_raw = item.get("hidden_tags", "")
            # 解析隐藏标签字符串
            item_hidden_tag_keys = []
            if isinstance(item_hidden_tags_raw, str) and item_hidden_tags_raw:
                # 分割 | 获取各个标签
                tag_parts = [t.strip() for t in item_hidden_tags_raw.split("|")]
                for tag_part in tag_parts:
                    # 提取英文部分
                    if " / " in tag_part:
                        tag_key = tag_part.split(" / ")[0].strip()
                        item_hidden_tag_keys.append(tag_key)
                    else:
                        item_hidden_tag_keys.append(tag_part.strip())
            
            if self.match_mode == "all":
                for tag in self.selected_hidden_tags:
                    if tag not in item_hidden_tag_keys:
                        return False
            else:  # any
                has_any = False
                for tag in self.selected_hidden_tags:
                    if tag in item_hidden_tag_keys:
                        has_any = True
                        break
                if not has_any:
                    return False
        
        return True
    
    def _on_scroll(self, value):
        """滚动事件 - 实现懒加载"""
        scrollbar = self.sender()
        if scrollbar.maximum() > 0:
            # ✅ 当滚动到50%时，预加载下一批（原80%）
            if value >= scrollbar.maximum() * 0.5:
                self._load_more_results()
    
    def _load_more_results(self):
        """加载更多结果 - 同步批量加载，使用蒙版提示"""
        if self.displayed_count >= len(self.search_results):
            return  # 已经全部加载
        
        # ✅ 防止重复触发加载
        if hasattr(self, '_is_loading') and self._is_loading:
            return
        
        # 计算本批次要加载的数量
        remaining = len(self.search_results) - self.displayed_count
        batch = min(self.batch_size, remaining)
        
        # 获取本批次的数据
        start_idx = self.displayed_count
        end_idx = start_idx + batch
        batch_items = self.search_results[start_idx:end_idx]
        
        # ✅ 改为同步加载所有卡片（避免高度闪烁），但添加到布局前统一创建
        cards = []
        for item in batch_items:
            item_id = item.get("id")
            # ✅ 根据当前搜索类型判断
            item_type = "skill" if self.search_query["item_type"] == "skill" else "item"
            tier = item.get("starting_tier", "").split(" / ")[0].lower() if item.get("starting_tier") else ""
            
            card = ItemDetailCard(
                item_id=item_id,
                item_type=item_type,
                current_tier=tier,
                default_expanded=False,
                enable_tier_click=False,
                content_scale=1.0,
                item_data=item
            )
            cards.append(card)
        
        # ✅ 统一添加所有卡片到布局（避免逐个添加导致的高度闪烁）
        for card in cards:
            self.results_layout.addWidget(card)
        
        self.displayed_count += batch
    
    def _update_results_display(self):
        """更新结果显示 - 使用懒加载机制"""
        # ✅ 显示加载蒙版
        self._show_loading()
        
        # 清空现有结果
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 重置显示计数和加载状态
        self.displayed_count = 0
        self._is_loading = False  # ✅ 重置加载标志
        
        if not self.search_results:
            # 显示空状态
            empty_label = QLabel("未找到匹配的物品\n\n尝试调整搜索条件")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("""
                QLabel {
                    font-family: 'Microsoft YaHei UI';
                    font-size: 16px;
                    color: #888888;
                    padding: 50px;
                }
            """)
            self.results_layout.addWidget(empty_label)
            # ✅ 隐藏加载蒙版
            self._hide_loading()
        else:
            # ✅ 使用QTimer延迟加载，确保UI刷新
            from PySide6.QtCore import QTimer
            QTimer.singleShot(50, self._perform_initial_load)
        
        # ✅ 移除stretch，让卡片自然排列不被拉伸
        # self.results_layout.addStretch()
    
    def _perform_initial_load(self):
        """执行初始加载并隐藏蒙版"""
        self._load_more_results()
        # ✅ 加载完成后隐藏蒙版
        self._hide_loading()
    
    def _show_loading(self):
        """显示加载蒙版和动画"""
        if hasattr(self, 'loading_overlay'):
            # ✅ 调整蒙版大小以覆盖整个父容器
            parent = self.loading_overlay.parent()
            if parent:
                self.loading_overlay.setGeometry(0, 0, parent.width(), parent.height())
            self.loading_overlay.raise_()  # 置顶显示
            self.loading_overlay.show()
            # 启动旋转动画
            self.loading_rotation = 0
            self.loading_timer.start(50)  # 每50ms更新一次
    
    def _hide_loading(self):
        """隐藏加载蒙版"""
        if hasattr(self, 'loading_overlay'):
            self.loading_overlay.hide()
            self.loading_timer.stop()
    
    def _update_loading_animation(self):
        """更新加载动画旋转 - 使用更明显的Unicode字符"""
        self.loading_rotation = (self.loading_rotation + 1) % 8
        # 使用更明显的旋转动画字符
        symbols = ["◜", "◝", "◞", "◟", "◜", "◝", "◞", "◟"]
        dots = ["   ", ".  ", ".. ", "..."]
        symbol = symbols[self.loading_rotation]
        dot = dots[self.loading_rotation % 4]
        self.loading_label.setText(f"{symbol} 加载中{dot}")
    
    def update_language(self):
        """更新语言（响应全局语言切换）"""
        # 重新渲染所有已显示的卡片
        for i in range(self.results_layout.count()):
            item = self.results_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, ItemDetailCard):
                    widget.update_language()
    
    def _on_splitter_moved(self, pos, index):
        """保存splitter位置"""
        sizes = self.splitter.sizes()
        self.config["encyclopedia_splitter_sizes"] = sizes
        self._save_config()
    
    def _restore_splitter_state(self):
        """恢复splitter位置"""
        if "encyclopedia_splitter_sizes" in self.config:
            sizes = self.config["encyclopedia_splitter_sizes"]
            if len(sizes) == 2:
                self.splitter.setSizes(sizes)
    
    def _on_container_resized(self, event, container):
        """容器大小改变时调整蒙版大小"""
        if hasattr(self, 'loading_overlay') and self.loading_overlay.isVisible():
            self.loading_overlay.setGeometry(0, 0, container.width(), container.height())
        # 调用原始的resizeEvent（如果有）
        QWidget.resizeEvent(container, event)
    
    def refresh(self):
        """刷新页面"""
        self._perform_search()
