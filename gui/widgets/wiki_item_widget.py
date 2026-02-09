"""
百科搜索卡片组件 - 单个物品/技能条目
"""
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter, QPainterPath
from pathlib import Path


class FlowLayout(QHBoxLayout):
    """流式布局 - 标签自动换行"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSpacing(4)
        self.setContentsMargins(0, 0, 0, 0)


class WikiItemWidget(QFrame):
    """
    百科搜索卡片组件
    
    布局结构：
    [图片(64x64)] [名称 + 品级标签]  [英雄头像(32x32)]
                   [属性标签组]
    """
    
    def __init__(self, item_data: dict, scale: float = 1.0, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self.scale = scale
        
        self.setObjectName("WikiItemCard")
        self.setFixedHeight(int(88 * scale))  # 固定高度
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # ✅ 核心样式：默认透明，hover时左金边+背景变亮
        self.setStyleSheet("""
            #WikiItemCard {
                background: #25211E;
                border: none;
                border-left: 0px solid transparent;
                border-radius: 4px;
            }
            #WikiItemCard:hover {
                background: #322C28;
                border-left: 3px solid #FFCC00;
            }
        """)
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            int(12 * self.scale), 
            int(8 * self.scale), 
            int(12 * self.scale), 
            int(8 * self.scale)
        )
        layout.setSpacing(int(12 * self.scale))
        
        # ✅ 左侧：图片容器（固定64x64，圆角4px）
        image_label = self._create_image_label()
        layout.addWidget(image_label)
        
        # ✅ 中间：垂直布局（名称+品级标签 / 属性标签组）
        middle_layout = QVBoxLayout()
        middle_layout.setSpacing(int(6 * self.scale))
        middle_layout.setContentsMargins(0, 0, 0, 0)
        
        # 第一行：名称 + 品级标签
        title_row = QHBoxLayout()
        title_row.setSpacing(int(8 * self.scale))
        title_row.setContentsMargins(0, 0, 0, 0)
        
        # 卡牌名称
        name_cn = self.item_data.get("name_cn", "")
        name_en = self.item_data.get("name", "")
        name_label = QLabel(name_cn or name_en)
        name_label.setStyleSheet(f"""
            font-family: 'Microsoft YaHei UI';
            font-size: {int(16 * self.scale)}px;
            font-weight: bold;
            color: white;
        """)
        title_row.addWidget(name_label)
        
        # 品级标签（如"青铜+"）
        tier_label = self._create_tier_label()
        if tier_label:
            title_row.addWidget(tier_label)
        
        title_row.addStretch()
        middle_layout.addLayout(title_row)
        
        # 第二行：属性标签组（FlowLayout自动换行）
        tags_layout = self._create_tags_layout()
        middle_layout.addLayout(tags_layout)
        
        middle_layout.addStretch()
        layout.addLayout(middle_layout, 1)
        
        # ✅ 右侧：英雄头像（圆形，32x32px）
        hero_avatar = self._create_hero_avatar()
        if hero_avatar:
            layout.addWidget(hero_avatar, 0, Qt.AlignmentFlag.AlignVCenter)
    
    def _create_image_label(self) -> QLabel:
        """创建图片容器 - 64x64，圆角4px"""
        label = QLabel()
        size = int(64 * self.scale)
        label.setFixedSize(size, size)
        
        # 加载图片
        item_id = self.item_data.get("id", "")
        item_type = self.item_data.get("type", "").lower()
        
        if item_type == "skill":
            image_dir = Path(__file__).parent.parent.parent / "assets" / "images" / "skill"
        else:
            image_dir = Path(__file__).parent.parent.parent / "assets" / "images" / "card"
        
        image_path = image_dir / f"{item_id}.webp"
        
        if image_path.exists():
            pixmap = QPixmap(str(image_path))
            # 缩放并应用圆角
            pixmap = pixmap.scaled(
                size, size, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            
            # 应用圆角蒙版
            rounded_pixmap = QPixmap(pixmap.size())
            rounded_pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(rounded_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            path = QPainterPath()
            path.addRoundedRect(0, 0, pixmap.width(), pixmap.height(), 4, 4)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            
            label.setPixmap(rounded_pixmap)
        else:
            label.setStyleSheet("""
                background: rgba(255, 255, 255, 0.05);
                border-radius: 4px;
            """)
        
        return label
    
    def _create_tier_label(self) -> QLabel:
        """创建品级标签 - 带背景色的小圆角矩形"""
        tier = self.item_data.get("tier", "").split(" / ")[0].lower()
        
        # 品级映射
        tier_map = {
            "bronze": ("青铜", "#cd7f32", "rgba(205, 127, 50, 0.2)"),
            "silver": ("白银", "#c0c0c0", "rgba(192, 192, 192, 0.2)"),
            "gold": ("黄金", "#ffd700", "rgba(255, 215, 0, 0.2)"),
            "diamond": ("钻石", "#b9f2ff", "rgba(185, 242, 255, 0.2)"),
            "legendary": ("传说", "#ff4500", "rgba(255, 69, 0, 0.2)")
        }
        
        if tier not in tier_map:
            return None
        
        tier_text, tier_color, tier_bg = tier_map[tier]
        
        # 检查是否有"+"后缀
        full_tier = self.item_data.get("tier", "")
        if " / " in full_tier:
            tier_text += "+"
        
        label = QLabel(tier_text)
        label.setStyleSheet(f"""
            font-family: 'Microsoft YaHei UI';
            font-size: {int(11 * self.scale)}px;
            font-weight: 800;
            color: {tier_color};
            background: {tier_bg};
            border: 1px solid {tier_color};
            border-radius: 3px;
            padding: 1px 6px;
        """)
        
        return label
    
    def _create_tags_layout(self) -> QHBoxLayout:
        """创建属性标签组 - FlowLayout布局"""
        layout = QHBoxLayout()
        layout.setSpacing(int(4 * self.scale))
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 获取标签
        tags = self.item_data.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        
        # 标签翻译映射（部分常用标签）
        tag_trans = {
            "Property": "地产", "Apparel": "服饰", "Tool": "工具", "Core": "核心",
            "Weapon": "武器", "Aquatic": "水系", "Toy": "玩具", "Tech": "科技",
            "Potion": "药水", "Food": "食物", "Vehicle": "载具", "Dragon": "龙",
            "Friend": "伙伴", "Dinosaur": "恐龙", "Loot": "战利品", "Relic": "遗物",
            "Ray": "射线", "Reagent": "原料"
        }
        
        # 只显示前5个标签
        for tag in tags[:5]:
            tag_text = tag_trans.get(tag, tag)
            tag_label = self._create_tag_pill(tag_text)
            layout.addWidget(tag_label)
        
        layout.addStretch()
        return layout
    
    def _create_tag_pill(self, text: str) -> QLabel:
        """创建单个标签Pill - 淡紫色背景"""
        label = QLabel(text)
        label.setStyleSheet(f"""
            font-family: 'Microsoft YaHei UI';
            font-size: {int(11 * self.scale)}px;
            color: rgba(152, 168, 254, 1);
            background: rgba(152, 168, 254, 0.15);
            border-radius: 3px;
            padding: 2px 8px;
        """)
        return label
    
    def _create_hero_avatar(self) -> QLabel:
        """创建英雄头像 - 圆形，32x32px"""
        heroes = self.item_data.get("heroes", [])
        if not heroes:
            return None
        
        # 取第一个英雄
        if isinstance(heroes, str):
            hero_key = heroes.split(" / ")[0]
        else:
            hero_key = heroes[0].split(" / ")[0] if heroes else None
        
        if not hero_key or hero_key == "Common":
            return None  # 通用物品不显示头像
        
        # 英雄头像映射
        hero_map = {
            "Pygmalien": "Pygmalien",
            "Jules": "Jules",
            "Vanessa": "Vanessa",
            "Mak": "Mak",
            "Dooley": "Dooley",
            "Stelle": "Stelle"
        }
        
        hero_name = hero_map.get(hero_key)
        if not hero_name:
            return None
        
        label = QLabel()
        size = int(32 * self.scale)
        label.setFixedSize(size, size)
        
        # 加载头像图片
        avatar_path = Path(__file__).parent.parent.parent / "assets" / "images" / "heroes" / f"{hero_name}.webp"
        
        if avatar_path.exists():
            pixmap = QPixmap(str(avatar_path))
            pixmap = pixmap.scaled(
                size, size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # 应用圆形蒙版
            rounded_pixmap = QPixmap(pixmap.size())
            rounded_pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(rounded_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            path = QPainterPath()
            path.addEllipse(0, 0, pixmap.width(), pixmap.height())
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            
            label.setPixmap(rounded_pixmap)
        
        return label
