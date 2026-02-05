# GUI组件重构说明文档

## 概述

本次重构将原有的廉价风格UI改造为参考旧版CSS的高品质游戏风格UI，主要特点：
- **酒馆褐色背景** - rgba(50, 45, 40, 0.6)
- **金色主题色** - #ffcc00
- **阶级边框** - 青铜/白银/黄金/钻石/传说
- **模块化组件** - 每个组件独立可复用

## 新增组件

### 1. MonsterDetailTooltip (怪物详情悬浮提示)

**文件**: `gui/components/monster_detail_tooltip.py`

**功能**: Hover到怪物卡片上时显示详细信息（技能、物品、属性等）

**使用方法**:
```python
from gui.components.monster_detail_tooltip import MonsterDetailTooltip

# 准备怪物数据
monster_data = {
    'id': 'monster_001',
    'name_zh': '史莱姆王',
    'hp': 150,
    'max_hp': 200,
    'available': [1, 2, 3, 4, 5],
    'bg_path': 'path/to/bg_image.webp',
    'char_path': 'path/to/char_image.webp',
    'skills': [
        {
            'name_zh': '粘液喷射',
            'size': 'medium',
            'cooldown': 3,
            'description': '向前方喷射粘液，造成伤害并降低移动速度',
            'image_path': 'path/to/skill.webp'
        }
    ],
    'items': [
        {
            'name_zh': '史莱姆核心',
            'size': 'small',
            'description': '史莱姆的能量核心',
            'image_path': 'path/to/item.webp'
        }
    ]
}

# 创建提示窗口（通常由MonsterCard自动管理）
tooltip = MonsterDetailTooltip(monster_data, parent=self)
tooltip.show()
```

**样式特点**:
- 半透明深色背景 rgba(50, 45, 40, 0.98)
- 金色边框强调
- 双层怪物头像（背景+角色）
- 技能和物品分栏显示
- 固定宽度450px，自适应高度

---

### 2. ItemDetailCard (物品详情卡片)

**文件**: `gui/components/item_detail_card.py`

**功能**: 统一的物品/技能详情展示组件，可展开/收起

**使用方法**:
```python
from gui.components.item_detail_card import ItemDetailCard

# 准备物品数据
item_data = {
    'name_zh': '烈焰长剑',
    'tier': 'gold',  # bronze, silver, gold, diamond, legendary
    'size': 'medium',  # small, medium, large
    'hero': '剑圣',
    'tags': ['武器', '火焰', '近战'],
    'cooldown': 5,
    'description': '附带火焰伤害的长剑，每次攻击都会灼烧敌人',
    'image_path': 'path/to/item.webp',
    'enchantments': [
        {
            'type': 'Damage',
            'effect': '+50 物理伤害'
        },
        {
            'type': 'Burn',
            'effect': '每秒造成15点火焰伤害，持续3秒'
        }
    ]
}

# 创建物品卡片
card = ItemDetailCard(item_data, parent=container)
card.detail_clicked.connect(self.show_full_detail)  # 可选：点击查看更多详情
```

**样式特点**:
- 阶级左边框（青铜#cd7f32, 白银#c0c0c0, 黄金#ffd700等）
- 酒馆风格背景渐变
- Hover高亮效果
- 展开显示CD时间和附魔列表
- 附魔类型带彩色徽章

---

### 3. MonsterCard (怪物简介卡片 - 重构版)

**文件**: `gui/components/monster_card.py` (已重构)

**功能**: 怪物简介展示，Hover自动显示详情提示

**使用方法**:
```python
from gui.components.monster_card import MonsterCard

monster_data = {
    'id': 'monster_001',
    'name_zh': '哥布林弓箭手',
    'hp': 80,
    'max_hp': 100,
    'available': [1, 2, 3],
    'bg_path': 'assets/images/monster_bg/goblin_bg.webp',
    'char_path': 'assets/images/monster_char/goblin_archer.webp',
    'skills': [...],  # 详情提示用
    'items': [...]    # 详情提示用
}

# 创建怪物卡片
card = MonsterCard(monster_data, parent=container)
card.clicked.connect(lambda mid: print(f"点击了怪物: {mid}"))

# 设置为已识别状态（高亮）
card.set_identified(True)
```

**样式特点**:
- 双层头像（背景+角色）
- Hover 500ms后自动显示详情提示
- 已识别状态金色发光边框
- 紧凑布局，适合列表展示

---

### 4. MonsterView (怪物一览视图)

**文件**: `gui/views/monster_view.py`

**功能**: 完整的怪物一览页面，集成天数选择和怪物列表

**使用方法**:
```python
from gui.views.monster_view import MonsterView

# 在Sidebar中使用
monster_view = MonsterView(parent=content_stack)
monster_view.scan_requested.connect(self.start_monster_scan)
monster_view.monster_clicked.connect(self.show_monster_detail)

# 设置怪物数据
monsters = [
    {
        'id': 'm1',
        'name_zh': '史莱姆',
        'hp': 100,
        'max_hp': 100,
        'available': [1, 2, 3],
        # ...
    },
    # ...
]
monster_view.set_monsters_data(monsters)

# 高亮指定怪物（识别成功后）
monster_view.highlight_monster('m1')
```

**布局结构**:
```
┌─────────────────────────┐
│  [Day Pills横向滚动]      │
│  [🔍 扫描当前怪物]        │
├─────────────────────────┤
│  ┌─────────────────┐    │
│  │ MonsterCard #1  │    │  (Hover显示详情)
│  ├─────────────────┤    │
│  │ MonsterCard #2  │    │
│  ├─────────────────┤    │
│  │ MonsterCard #3  │    │
│  │      ...        │    │
│  └─────────────────┘    │
└─────────────────────────┘
```

---

## 集成到SidebarWindow

### 修改sidebar_window.py

```python
# gui/windows/sidebar_window.py

from gui.views.monster_view import MonsterView
from gui.views.card_recognition_view import CardRecognitionView  # 你需要创建

class SidebarWindow(QWidget):
    def __init__(self):
        super().__init__()
        # ...现有代码...
        
    def _setup_ui(self):
        # ...现有代码...
        
        # === 右侧内容区域 ===
        self.content_area = QFrame()
        self.content_area.setObjectName("ContentArea")
        
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # 内容堆叠
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("ContentStack")
        
        # 添加各个页面
        self.monster_view = MonsterView()
        self.card_view = CardRecognitionView()  # 需要创建
        # ... 其他视图
        
        self.content_stack.addWidget(self.monster_view)  # 索引0
        self.content_stack.addWidget(self.card_view)     # 索引1
        # ...
        
        content_layout.addWidget(self.content_stack)
        container_layout.addWidget(self.content_area, 1)
        
        # 连接导航切换
        self.nav_group.buttonClicked.connect(self._on_nav_changed)
        
    def _on_nav_changed(self, button):
        """导航切换"""
        index = self.nav_group.buttons().index(button)
        self.content_stack.setCurrentIndex(index)
```

---

## 样式变量说明

### 颜色定义 (参考旧版CSS)

```python
# 阶级颜色
TIER_COLORS = {
    'bronze': '#CD7F32',
    'silver': '#C0C0C0',
    'gold': '#FFD700',
    'diamond': '#B9F2FF',
    'legendary': '#FF4500'
}

# 附魔颜色
ENCHANT_COLORS = {
    'Haste': 'rgb(0, 236, 195)',
    'Damage': 'rgb(245, 80, 61)',
    'Slow': 'rgb(203, 159, 110)',
    'Heal': 'rgb(142, 234, 49)',
    'Poison': 'rgb(14, 190, 79)',
    'Freeze': 'rgb(63, 200, 247)',
    'Shield': 'rgb(244, 207, 32)',
    'Burn': 'rgb(255, 159, 69)',
}

# 背景颜色
BG_COLORS = {
    'dark_brown': 'rgba(50, 45, 40, 0.6)',  # 主卡片背景
    'deep_black': 'rgba(0, 0, 0, 0.3)',     # 控制栏背景
    'hover_brown': 'rgba(70, 60, 40, 0.7)', # Hover状态
}
```

---

## 数据结构规范

### MonsterData (怪物数据)

```python
{
    'id': str,              # 怪物唯一ID
    'name_zh': str,         # 中文名称
    'name_en': str,         # 英文名称 (可选)
    'hp': int,              # 当前血量
    'max_hp': int,          # 最大血量
    'available': list[int], # 可用天数 [1,2,3...]
    'bg_path': str,         # 背景图片路径
    'char_path': str,       # 角色图片路径
    'skills': list[SkillData],  # 技能列表
    'items': list[ItemData]     # 物品列表
}
```

### SkillData/ItemData (技能/物品数据)

```python
{
    'name_zh': str,         # 中文名称
    'name_en': str,         # 英文名称 (可选)
    'size': str,            # 尺寸: 'small', 'medium', 'large'
    'cooldown': float,      # CD时间 (秒)
    'description': str,     # 描述文本
    'image_path': str,      # 图片路径
    'tier': str,            # 阶级 (仅物品): 'bronze', 'silver', 'gold', 'diamond', 'legendary'
    'hero': str,            # 所属英雄 (仅物品): '剑圣', '弓箭手', '通用'
    'tags': list[str],      # 标签列表 (仅物品)
    'enchantments': list[EnchantData]  # 附魔列表 (仅物品)
}
```

### EnchantData (附魔数据)

```python
{
    'type': str,    # 附魔类型: 'Haste', 'Damage', 'Heal', etc.
    'effect': str   # 效果描述: '+50 物理伤害'
}
```

---

## 下一步工作

1. **创建CardRecognitionView** - 卡牌识别页面
2. **创建HandItemsView** - 手头物品页面  
3. **创建SearchView** - 百科搜索页面
4. **创建RecommendView** - 阵容推荐页面
5. **创建AnalyticsView** - 策略分析页面

每个View都参考MonsterView的结构，使用ItemDetailCard展示物品。

---

## 注意事项

1. **图片路径**: 所有image_path需要使用绝对路径或相对于项目根目录的路径
2. **数据源**: 需要从后端API获取真实数据，当前示例使用mock数据
3. **性能优化**: 怪物列表较长时，考虑使用虚拟滚动或分页加载
4. **字体缩放**: 所有组件已支持字体缩放（通过QSS的calc()）
5. **Tooltip位置**: MonsterDetailTooltip默认显示在卡片右侧，屏幕边缘时需调整位置

---

## 测试清单

- [ ] MonsterCard Hover显示详情
- [ ] MonsterCard 点击发送信号
- [ ] MonsterCard 已识别状态高亮
- [ ] ItemDetailCard 展开/收起功能
- [ ] ItemDetailCard 阶级边框正确显示
- [ ] MonsterView 天数切换过滤怪物
- [ ] MonsterView 扫描按钮触发信号
- [ ] MonsterView 高亮指定怪物

---

**作者**: GitHub Copilot  
**日期**: 2026-02-05  
**版本**: 1.0
