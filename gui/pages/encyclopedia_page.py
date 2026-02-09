"""
百科搜索页面 - 完全照抄React版本
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QScrollArea, QSplitter
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPixmap, QIcon
from pathlib import Path
import json
from gui.widgets.item_detail_card_v2 import ItemDetailCard
from gui.widgets.flow_layout import FlowLayout


class EncyclopediaPage(QWidget):
    """百科搜索页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
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
        self.match_mode = "all"  # all 或 any
        self.is_filter_collapsed = False
        
        # 搜索结果
        self.search_results = []
        self.is_searching = False
        
        # 记住上次物品尺寸（用于类型切换）
        self.last_item_size = ""
        
        # 初始化按钮字典
        self.type_buttons = {}
        self.size_buttons = {}
        self.tier_buttons = {}
        self.hero_buttons = {}
        self.tag_buttons = {}
        self.hidden_tag_buttons = {}
        
        # 加载数据
        self.items_db = self._load_items_db()
        
        # 防抖定时器
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)
        
        # 读取配置
        self.config_path = Path("user_data/user_config.json")
        self.config = self._load_config()
        
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
        
        # 结果容器
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(15, 15, 15, 15)
        self.results_layout.setSpacing(8)
        
        scroll_area.setWidget(self.results_container)
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
        container_layout.setContentsMargins(12, 12, 12, 12)
        container_layout.setSpacing(8)
        
        # 标题行（带折叠按钮）
        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        
        # 左侧：标题 + 匹配模式按钮
        left_group = QHBoxLayout()
        left_group.setSpacing(8)
        
        title_label = QLabel("搜索过滤器")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #ffcd19;
                font-weight: bold;
            }
        """)
        left_group.addWidget(title_label)
        
        # 匹配模式按钮组
        self.btn_match_all = self._create_toggle_button("匹配所有", active=True)
        self.btn_match_all.clicked.connect(lambda: self._set_match_mode("all"))
        left_group.addWidget(self.btn_match_all)
        
        self.btn_match_any = self._create_toggle_button("匹配任一", active=False)
        self.btn_match_any.clicked.connect(lambda: self._set_match_mode("any"))
        left_group.addWidget(self.btn_match_any)
        
        header_row.addLayout(left_group)
        header_row.addStretch()
        
        # 折叠按钮
        self.collapse_btn = QPushButton("收起 ▲")
        self.collapse_btn.setFixedSize(80, 28)
        self.collapse_btn.clicked.connect(self._toggle_filter_collapse)
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
        header_row.addWidget(self.collapse_btn)
        
        container_layout.addLayout(header_row)
        
        # 过滤器内容（可折叠）
        self.filter_content = QWidget()
        filter_content_layout = QVBoxLayout(self.filter_content)
        filter_content_layout.setContentsMargins(0, 0, 0, 0)
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
        
        # 第2行：类型按钮（物品/技能）
        type_row = QVBoxLayout()
        type_row.setSpacing(6)
        
        type_title = QLabel("类型")
        type_title.setStyleSheet("font-size: 11px; color: #888; font-weight: bold;")
        type_row.addWidget(type_title)
        
        type_container = QWidget()
        type_layout = FlowLayout(type_container, h_spacing=6, v_spacing=6)
        
        self.type_buttons = {}
        for type_val, label in [("item", "物品"), ("skill", "技能")]:
            btn = self._create_toggle_button(label)
            btn.clicked.connect(lambda checked, t=type_val: self._set_item_type(t))
            type_layout.addWidget(btn)
            self.type_buttons[type_val] = btn
        
        type_row.addWidget(type_container)
        filter_content_layout.addLayout(type_row)
        
        # 第3行：尺寸
        size_row = QVBoxLayout()
        size_row.setSpacing(6)
        
        size_title = QLabel("尺寸")
        size_title.setStyleSheet("font-size: 11px; color: #888; font-weight: bold;")
        size_row.addWidget(size_title)
        
        # 尺寸按钮组（只在选择物品时显示）
        self.size_group_widget = QWidget()
        size_layout = FlowLayout(self.size_group_widget, h_spacing=6, v_spacing=6)
        
        self.size_buttons = {}
        for size_val, label in [("small", "小"), ("medium", "中"), ("large", "大")]:
            btn = self._create_toggle_button(label)
            btn.clicked.connect(lambda checked, s=size_val: self._set_size(s))
            size_layout.addWidget(btn)
            self.size_buttons[size_val] = btn
        
        size_row.addWidget(self.size_group_widget)
        filter_content_layout.addLayout(size_row)
        
        # 第4行：品级
        tier_row = QVBoxLayout()
        tier_row.setSpacing(6)
        
        tier_title = QLabel("品级")
        tier_title.setStyleSheet("font-size: 11px; color: #888; font-weight: bold;")
        tier_row.addWidget(tier_title)
        
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
        
        tier_row.addWidget(tier_container)
        filter_content_layout.addLayout(tier_row)
        
        # 第5行：英雄选择
        hero_row = QVBoxLayout()
        hero_row.setSpacing(6)
        
        hero_title = QLabel("英雄")
        hero_title.setStyleSheet("font-size: 11px; color: #888; font-weight: bold;")
        hero_row.addWidget(hero_title)
        
        hero_container = QWidget()
        hero_layout = FlowLayout(hero_container, h_spacing=6, v_spacing=6)
        
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
        
        hero_row.addWidget(hero_container)
        filter_content_layout.addLayout(hero_row)
        
        # ✅ 第6行：标签（可多选）- 固定横向布局+横向滚动
        row6 = QVBoxLayout()
        row6.setSpacing(8)
        
        tag_title = QLabel("标签 (可多选)")
        tag_title.setStyleSheet("font-size: 11px; color: #888;")
        row6.addWidget(tag_title)
        
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
        
        # 固定横向布局
        tag_widget = QWidget()
        tag_layout = QHBoxLayout(tag_widget)
        tag_layout.setContentsMargins(0, 0, 0, 0)
        tag_layout.setSpacing(6)
        
        for val, label in tags:
            btn = self._create_toggle_button(label)
            btn.setProperty("tag_val", val)
            btn.clicked.connect(lambda checked, v=val: self._toggle_tag(v))
            tag_layout.addWidget(btn)
            self.tag_buttons[val] = btn
        
        tag_layout.addStretch()
        
        # ✅ 允许自动换行，不限制高度
        tag_widget.setLayout(tag_layout)
        row6.addWidget(tag_widget)
        filter_content_layout.addLayout(row6)
        
        # 第7行：隐藏标签（可多选）
        hidden_tag_row = QVBoxLayout()
        hidden_tag_row.setSpacing(6)
        
        hidden_tag_title = QLabel("隐藏标签 (可多选)")
        hidden_tag_title.setStyleSheet("font-size: 11px; color: #888; font-weight: bold;")
        hidden_tag_row.addWidget(hidden_tag_title)
        
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
        
        hidden_tag_row.addWidget(hidden_tag_container)
        filter_content_layout.addLayout(hidden_tag_row)
        
        container_layout.addWidget(self.filter_content)
        
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
        
        # ✅ 设置最小宽度以确保文字完整显示
        btn.setMinimumWidth(60)
        
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
            btn.setText(label)
            btn.setFixedSize(60, 32)
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
    
    def _toggle_filter_collapse(self):
        """切换过滤器折叠状态"""
        self.is_filter_collapsed = not self.is_filter_collapsed
        self.filter_content.setVisible(not self.is_filter_collapsed)
        self.collapse_btn.setText("展开 ▼" if self.is_filter_collapsed else "收起 ▲")
    
    def _set_match_mode(self, mode: str):
        """设置匹配模式"""
        self.match_mode = mode
        self.btn_match_all.setProperty("active", mode == "all")
        self.btn_match_all.style().unpolish(self.btn_match_all)
        self.btn_match_all.style().polish(self.btn_match_all)
        
        self.btn_match_any.setProperty("active", mode == "any")
        self.btn_match_any.style().unpolish(self.btn_match_any)
        self.btn_match_any.style().polish(self.btn_match_any)
        
        self._debounced_search()
    
    def _set_item_type(self, type_val: str):
        """设置物品类型"""
        # 切换逻辑：点击已激活的按钮则取消选择
        if self.search_query["item_type"] == type_val:
            self.search_query["item_type"] = "all"
            # 恢复尺寸
            if type_val == "skill":
                self.search_query["size"] = self.last_item_size
        elif type_val == "skill":
            # 切换到技能：隐藏尺寸筛选
            self.last_item_size = self.search_query["size"]
            self.search_query["item_type"] = "skill"
            self.search_query["size"] = ""
            self.size_group_widget.setVisible(False)
        else:
            # 切换到物品：显示尺寸筛选
            self.search_query["item_type"] = type_val
            if self.search_query.get("size") == "" and self.last_item_size:
                self.search_query["size"] = self.last_item_size
            self.size_group_widget.setVisible(True)
        
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
            "item_type": "all",
            "size": "",
            "start_tier": "",
            "hero": "",
        }
        self.selected_tags = []
        self.selected_hidden_tags = []
        self.match_mode = "all"
        
        # 重置UI
        self.keyword_input.clear()
        
        # 重置按钮状态
        for btn in self.type_buttons.values():
            btn.setProperty("active", False)
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
        self._set_match_mode("all")
        self._perform_search()
    
    def _perform_search(self):
        """执行搜索"""
        self.is_searching = True
        self.stats_label.setText("🔍 搜索中...")
        
        # 过滤逻辑
        results = []
        for item in self.items_db:
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
        # 关键词匹配
        if self.search_query["keyword"]:
            keyword = self.search_query["keyword"].lower()
            name_match = keyword in item.get("name", "").lower() or keyword in item.get("name_cn", "").lower()
            desc_match = False
            
            # 搜索描述（包括skills）
            skills = item.get("skills", [])
            for skill in skills:
                if isinstance(skill, str) and keyword in skill.lower():
                    desc_match = True
                    break
            
            if not (name_match or desc_match):
                return False
        
        # 类型匹配
        if self.search_query["item_type"] != "all":
            item_type = item.get("type", "").lower()
            if self.search_query["item_type"] == "skill" and item_type != "skill":
                return False
            elif self.search_query["item_type"] == "item" and item_type == "skill":
                return False
        
        # 尺寸匹配
        if self.search_query["size"]:
            size = item.get("size", "").split(" / ")[0].lower()
            if size != self.search_query["size"]:
                return False
        
        # 品级匹配
        if self.search_query["start_tier"]:
            tier = item.get("tier", "").split(" / ")[0].lower()
            if tier != self.search_query["start_tier"]:
                return False
        
        # 英雄匹配
        if self.search_query["hero"]:
            heroes = item.get("heroes", [])
            if isinstance(heroes, str):
                heroes = [heroes]
            
            hero_match = False
            for hero in heroes:
                hero_key = hero.split(" / ")[0] if isinstance(hero, str) else str(hero)
                if hero_key == self.search_query["hero"]:
                    hero_match = True
                    break
            
            if not hero_match:
                return False
        
        # ✅ 标签匹配（普通标签）
        if self.selected_tags:
            item_tags = item.get("tags", [])
            if isinstance(item_tags, str):
                item_tags = [item_tags]
            
            if self.match_mode == "all":
                # 所有选中的标签都必须在物品标签中
                for tag in self.selected_tags:
                    if tag not in item_tags:
                        return False
            else:  # any
                # 至少有一个选中的标签在物品标签中
                has_any = False
                for tag in self.selected_tags:
                    if tag in item_tags:
                        has_any = True
                        break
                if not has_any:
                    return False
        
        # ✅ 隐藏标签匹配
        if self.selected_hidden_tags:
            item_hidden_tags = item.get("hidden_tags", [])
            if isinstance(item_hidden_tags, str):
                item_hidden_tags = [item_hidden_tags]
            
            if self.match_mode == "all":
                for tag in self.selected_hidden_tags:
                    if tag not in item_hidden_tags:
                        return False
            else:  # any
                has_any = False
                for tag in self.selected_hidden_tags:
                    if tag in item_hidden_tags:
                        has_any = True
                        break
                if not has_any:
                    return False
        
        return True
    
    def _update_results_display(self):
        """更新结果显示 - 使用ItemDetailCard（v2展开式卡片）"""
        # 清空现有结果
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
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
        else:
            # ✅ 使用ItemDetailCard显示结果（默认可展开）
            for item in self.search_results[:100]:  # 限制显示数量
                item_id = item.get("id")
                item_type = "skill" if item.get("type", "").lower() == "skill" else "item"
                tier = item.get("tier", "").split(" / ")[0].lower()
                
                card = ItemDetailCard(
                    item_id=item_id,
                    item_type=item_type,
                    current_tier=tier,
                    default_expanded=False,  # 默认折叠
                    enable_tier_click=False,
                    content_scale=1.0,
                    item_data=item
                )
                self.results_layout.addWidget(card)
        
        self.results_layout.addStretch()
    
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
    
    def refresh(self):
        """刷新页面"""
        self._perform_search()
