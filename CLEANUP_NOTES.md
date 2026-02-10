# 代码清理说明

## 废弃文件（可以删除）

以下文件已废弃，不再被使用，可以安全删除：

### 1. `gui/widgets/monster_detail_dialog.py`
- **原用途**: 怪物详情弹窗（旧版本）
- **当前状态**: 未被任何代码引用
- **替代方案**: 使用 `MonsterDetailFloatWindow`

### 2. `gui/widgets/monster_detail_content.py`
- **原用途**: 怪物详情内容组件（旧版本）
- **当前状态**: 未被任何代码引用
- **替代方案**: 使用 `MonsterDetailFloatWindow`

## 当前使用的文件

### `gui/widgets/monster_detail_float_window.py`
- **用途**: 怪物详情悬浮窗（唯一在用的版本）
- **使用位置**: `gui/pages/monster_overview_page.py`
- **功能**: 
  - 显示怪物完整信息（头像、血量、技能、掉落物品）
  - 点击掉落物品时，在下方展开显示物品详情
  - 可拖拽、可调整大小
  - 支持内容缩放

## 最新改动（2026-02-09）

### 移除 Hover 显示逻辑
- **旧逻辑**: Hover 在掉落物品图标上时，弹出独立的物品详情窗口（会出现白框闪烁bug）
- **新逻辑**: 点击掉落物品图标，在怪物悬浮框内部的掉落物品下方直接展开 ItemDetailCard
- **优点**: 
  - 无白框闪烁
  - 所有内容在一个窗口内，滚动查看
  - 点击同一物品可收起详情
  - 点击不同物品自动切换显示

### 实现细节
- 移除了 `InlineItemLabel` 类中的 `enterEvent`、`leaveEvent`、`_show_timer`、`_hide_timer` 等 hover 相关代码
- 移除了 `_do_show_popup`、`_hide_popup` 等弹窗方法
- 保留了 `mousePressEvent`，改为调用 `_toggle_item_detail` 方法
- `_toggle_item_detail` 方法直接在 `content_layout` 中插入/移除 `ItemDetailCard`，不使用额外容器
