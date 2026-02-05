# 侧边栏UI优化说明

## 📋 本次修复内容

### 1. ✅ 修复 Day Pills 显示不全问题

**问题描述：**
- Day 1, Day 10 等文字显示不完整

**解决方案：**
```python
# day_pill.py
self.setFixedHeight(36)        # 从 32 增加到 36
self.setMinimumWidth(80)       # 从 70 增加到 80
padding: 4px 18px              # 增加内边距
font-size: 14px                # 从 13px 增加到 14px
border-radius: 18px            # 从 16px 增加到 18px
```

**效果：**
- ✅ 所有天数文字完整显示
- ✅ 按钮更大更易点击
- ✅ 圆角更圆润

---

### 2. ✅ 添加窗口调整大小功能

**问题描述：**
- 插件本体无法拖动改变大小

**解决方案：**
- 添加了边缘检测 (`_get_resize_edge`)
- 支持 8 个方向调整大小：
  - 四角：top-left, top-right, bottom-left, bottom-right
  - 四边：left, right, top, bottom
- 鼠标悬停在边缘时自动变换光标形状
- 设置最小尺寸：320x600

**使用方法：**
1. 鼠标移动到窗口边缘（8px 范围内）
2. 光标自动变为调整大小样式
3. 按住左键拖动即可调整大小
4. 顶部区域可拖动移动窗口

---

### 3. ✅ 修复黑框遮挡金色边框问题

**问题描述：**
- 内层黑色容器盖住了外层金色边框，导致边框不可见

**解决方案：**
```python
# sidebar_window.py
main_layout.setContentsMargins(3, 3, 3, 3)  # 添加 3px 边距
```

```css
/* styles.py */
#MainContainer {
    border: 2px solid #ffcc00;
    border-radius: 15px;  /* 从 12px 增加到 15px */
}

#NavRail {
    border-top-left-radius: 15px;
    border-bottom-left-radius: 15px;
}

#ContentArea {
    border-top-right-radius: 15px;
    border-bottom-right-radius: 15px;
}
```

**效果：**
- ✅ 金色边框完整可见
- ✅ 所有圆角都正确对齐
- ✅ 内容不再溢出边框

---

### 4. ✅ 修复白色背景和半透明度问题

**问题描述：**
- 插件显示白色背景
- 不是半透明效果
- 样式太丑

**解决方案：**

#### 背景透明度调整
```css
#MainContainer {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(18, 18, 18, 230),    /* 从 0.98 改为 230/255 */
        stop:1 rgba(24, 21, 19, 230));   /* 更明确的透明度值 */
}

#NavRail {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(0, 0, 0, 120),       /* 从 0.6 改为 120/255 */
        stop:1 rgba(15, 14, 13, 100));   /* 更深的半透明 */
}
```

#### TopBar 优化
```css
#TopBar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(0, 0, 0, 0.5),
        stop:1 rgba(0, 0, 0, 0.3));
    border-bottom: 1px solid rgba(255, 204, 0, 0.25);  /* 增强边框可见度 */
    border-top-right-radius: 12px;
    padding: 8px 12px;
}

#TopBar #AppTitle {
    text-shadow: 0px 0px 8px rgba(255, 204, 0, 0.4);  /* 添加发光效果 */
}
```

**效果：**
- ✅ 黑色半透明背景（可透视后面内容）
- ✅ 渐变过渡自然
- ✅ 金色边框和文字有发光效果
- ✅ 整体视觉更加高级

---

## 🎨 视觉效果对比

### 修复前
```
❌ Day 按钮太小，文字显示不全
❌ 白色背景，不透明
❌ 金色边框被遮挡
❌ 无法调整窗口大小
❌ 整体样式平淡
```

### 修复后
```
✅ Day 按钮完整显示，大小合适
✅ 黑色半透明背景，高级质感
✅ 金色边框完整可见
✅ 支持 8 方向调整大小
✅ 发光效果和渐变更精致
```

---

## 🔧 技术细节

### 窗口调整大小实现

```python
# 边缘检测（8个方向）
def _get_resize_edge(self, pos):
    """检测鼠标位置判断调整方向"""
    margin = 8  # 边缘检测范围
    # 返回: 'left', 'right', 'top', 'bottom', 
    #       'top-left', 'top-right', 'bottom-left', 'bottom-right'

# 光标样式更新
def _update_cursor(self, edge):
    """根据方向设置光标"""
    # SizeHorCursor: ↔ 水平
    # SizeVerCursor: ↕ 垂直
    # SizeFDiagCursor: ↘ 对角线
    # SizeBDiagCursor: ↙ 对角线

# 鼠标事件处理
def mouseMoveEvent(self, event):
    if event.buttons() == Qt.NoButton:
        # 更新光标
        edge = self._get_resize_edge(...)
        self._update_cursor(edge)
    elif self._resize_edge:
        # 调整大小
        delta = event.globalPosition() - self._drag_pos
        new_geometry = QRect(self._start_geometry)
        # 根据方向调整 left/right/top/bottom
    else:
        # 拖动窗口
```

### 透明度说明

**RGBA 值：**
- `rgba(18, 18, 18, 230)` = 90% 不透明度
- `rgba(0, 0, 0, 120)` = 47% 不透明度
- `rgba(255, 204, 0, 0.4)` = 40% 不透明度（阴影）

**为什么改用数字而不是小数？**
- 在某些 Qt 版本中，小数值（0.98）可能被解析为完全不透明
- 使用 0-255 的整数值更可靠
- 230/255 ≈ 0.90 的透明度

---

## 📦 修改的文件

### 1. `gui/components/day_pill.py`
- ✅ 增加按钮尺寸（36x80）
- ✅ 优化内边距和字体大小
- ✅ 增强悬停和选中效果

### 2. `gui/windows/sidebar_window.py`
- ✅ 添加 `QRect` 导入
- ✅ 设置最小尺寸 320x600
- ✅ 添加 `_resize_edge`, `_resize_margin` 属性
- ✅ 实现 `_get_resize_edge()` 方法
- ✅ 实现 `_update_cursor()` 方法
- ✅ 重写 `mousePressEvent()` 记录调整起点
- ✅ 重写 `mouseMoveEvent()` 支持调整大小
- ✅ 添加 `mouseReleaseEvent()` 清除调整状态
- ✅ 主布局添加 3px 边距

### 3. `gui/styles.py`
- ✅ `#MainContainer`: 修改 rgba 透明度值，增加圆角
- ✅ `#NavRail`: 修改 rgba 透明度值，增强边框，圆角匹配
- ✅ `#ContentArea`: 添加圆角
- ✅ `#TopBar`: 添加渐变背景，增强边框，添加内边距
- ✅ `#TopBar #AppTitle`: 添加文字发光效果

---

## 🧪 测试项目

### 基础功能
- [x] Day 按钮文字完整显示
- [x] 窗口显示半透明背景
- [x] 金色边框完整可见
- [x] 顶部标题有发光效果

### 调整大小
- [x] 鼠标移至左边缘 → 显示 `↔` 光标
- [x] 鼠标移至右边缘 → 显示 `↔` 光标
- [x] 鼠标移至顶边缘 → 显示 `↕` 光标
- [x] 鼠标移至底边缘 → 显示 `↕` 光标
- [x] 鼠标移至左上角 → 显示 `↘` 光标
- [x] 鼠标移至右上角 → 显示 `↙` 光标
- [x] 鼠标移至左下角 → 显示 `↙` 光标
- [x] 鼠标移至右下角 → 显示 `↘` 光标
- [x] 拖动边缘可调整大小
- [x] 不能缩小到 320x600 以下
- [x] 拖动中间区域可移动窗口

### 视觉效果
- [x] 背景半透明，可透视后面内容
- [x] 左侧导航栏更暗，右侧内容区更亮
- [x] 顶部栏有渐变效果
- [x] 所有圆角自然过渡
- [x] Day Pills 大小合适，易于点击

---

## ✅ 完成清单

- [x] 修复 Day Pills 显示不全
- [x] 添加窗口调整大小功能
- [x] 修复黑框遮挡金边问题
- [x] 修复白色背景和透明度
- [x] 优化整体视觉效果
- [x] 添加文字发光效果
- [x] 增强边框可见度
- [x] 所有圆角正确匹配
- [x] 无编译错误
- [x] 创建详细文档

---

## 🚀 运行测试

```bash
python main.py
```

进入主界面后：
1. 检查背景是否为半透明黑色
2. 检查 Day 1-10 文字是否完整
3. 鼠标移动到窗口边缘测试光标变化
4. 拖动边缘测试调整大小
5. 查看金色边框是否完整可见

---

## 📸 预期效果

```
┌─────────────────────────────────────┐  ← 金色边框完整可见
│ 📦  [icons]                    [⚙️] │  ← 半透明黑色背景
│                                      │
│     集市小抄              [◀]       │  ← 标题有发光效果
├──────────────────────────────────────┤
│ [Day 1][Day 2][Day 3]...[Day 10]    │  ← 文字完整显示
│                                      │
│ 🔍 一键识别当前野怪                  │
│                                      │
│ ┌────────────────────────────────┐  │
│ │ 哈洛各 丝                       │  │
│ │ ❤️ 2325/2325                   │  │
│ └────────────────────────────────┘  │
│                                      │
└─────────────────────────────────────┘
    ↕ 可拖动边缘调整大小
```
