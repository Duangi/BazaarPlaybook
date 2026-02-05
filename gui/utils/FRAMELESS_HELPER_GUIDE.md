# FramelessHelper 使用指南

## 📚 简介

`FramelessHelper` 是一个基于事件过滤器的窗口助手类，采用 **Helper/Controller 模式**，为任何 QWidget 添加拖拽和调整大小功能，无需修改继承关系。

## 🎯 为什么使用 Helper 模式？

### 传统 Mixin 模式的问题
```python
# ❌ 需要修改继承关系
class MyWindow(QWidget, DraggableMixin, ResizableMixin):
    def __init__(self):
        super().__init__()
        self.setup_draggable()
        self.setup_resizable()
        # 需要覆盖 mousePressEvent/Move/Release
```

**问题：**
- 改变了类的继承结构
- 多个 Mixin 之间可能有事件冲突
- 难以在运行时动态启用/禁用功能

### Helper 模式的优势
```python
# ✅ 一行代码搞定，不改变继承关系
class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.helper = FramelessHelper(self, margin=8, snap_to_top=True)
```

**优势：**
- ✅ 不改变类的继承结构
- ✅ 使用事件过滤器，不会与子控件的事件冲突
- ✅ 可以动态启用/禁用功能
- ✅ 代码更简洁，维护更容易

## 📖 基础用法

### 1️⃣ 最简单的用法

```python
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
from gui.utils.frameless_helper import FramelessHelper

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        # 设置无边框
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # ✅ 一行代码启用拖拽和调整大小
        self.helper = FramelessHelper(self)
        
        # 设置最小尺寸（防止用户缩得太小）
        self.setMinimumSize(300, 400)
```

### 2️⃣ 自定义参数

```python
self.helper = FramelessHelper(
    self,
    margin=8,           # 边缘检测区域宽度（像素）
    snap_to_top=True,   # 启用顶部吸附
    enable_drag=True,   # 启用拖拽
    enable_resize=True  # 启用调整大小
)

# 设置尺寸限制
self.setMinimumSize(400, 300)  # 最小尺寸
self.setMaximumSize(1200, 900)  # 最大尺寸
```

### 3️⃣ 只需要拖拽，不需要调整大小

```python
self.helper = FramelessHelper(
    self,
    snap_to_top=True,
    enable_drag=True,
    enable_resize=False  # ❌ 禁用调整大小
)
```

### 4️⃣ 只需要调整大小，不需要拖拽

```python
self.helper = FramelessHelper(
    self,
    enable_drag=False,   # ❌ 禁用拖拽
    enable_resize=True,
    margin=10  # 更宽的边缘检测区域
)
```

## 🔧 动态控制功能

Helper 支持运行时动态调整参数：

```python
class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.helper = FramelessHelper(self)
    
    def lock_window(self):
        """锁定窗口（不可拖拽和调整大小）"""
        self.helper.set_draggable(False)
        self.helper.set_resizable(False)
    
    def unlock_window(self):
        """解锁窗口"""
        self.helper.set_draggable(True)
        self.helper.set_resizable(True)
    
    def toggle_snap(self):
        """切换顶部吸附"""
        current = self.helper.snap_to_top
        self.helper.set_snap_to_top(not current)
```

## 🎨 工作原理

### 边缘检测逻辑

```
┌─────────────────────────────┐
│ ↖  TopEdge (8px)        ↗  │  ← 角落：对角线调整大小
│                             │
│ L                         R │  ← 边缘：水平/垂直调整大小
│ e     中央区域（拖拽）      i │
│ f                         g │
│ t                         h │
│                             │
│ ↙  BottomEdge (8px)     ↘  │
└─────────────────────────────┘
```

**区域划分：**
- **边缘区域**（margin=8px）：调整大小，光标变化
  - 左/右边缘：`Qt.SizeHorCursor` ↔
  - 上/下边缘：`Qt.SizeVerCursor` ↕
  - 左上/右下角：`Qt.SizeFDiagCursor` ↖↘
  - 右上/左下角：`Qt.SizeBDiagCursor` ↗↙
- **中央区域**：拖拽窗口

### 事件过滤器机制

```python
def eventFilter(self, obj, event):
    # 拦截目标窗口的鼠标事件
    if event.type() == QEvent.MouseButtonPress:
        self._handle_press(event)  # 判断点击位置
    elif event.type() == QEvent.MouseMove:
        self._handle_move(event)   # 执行拖拽或调整大小
    elif event.type() == QEvent.MouseButtonRelease:
        self._handle_release(event)  # 结束操作
    
    return False  # ✅ 返回 False，让事件继续传递给子控件
```

**优势：**
- 不覆盖窗口的 `mousePressEvent` 等方法
- 子控件（按钮、输入框等）的事件不受影响
- 更符合 Qt 的事件处理最佳实践

## 💡 实际应用示例

### Sidebar 窗口（完整示例）

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from gui.utils.frameless_helper import FramelessHelper

class SidebarWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        # 设置无边框窗口
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # ✅ 启用拖拽和调整大小
        self.helper = FramelessHelper(
            self,
            margin=8,
            snap_to_top=True
        )
        
        # 设置尺寸限制
        self.setMinimumSize(400, 500)
        self.setMaximumSize(800, 1200)
        
        # 初始化 UI
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        label = QLabel("拖动我 or 调整大小！")
        layout.addWidget(label)
```

### 对话框窗口（可拖拽，不可调整大小）

```python
class CustomDialog(QDialog):
    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # 只启用拖拽
        self.helper = FramelessHelper(
            self,
            enable_drag=True,
            enable_resize=False  # 固定大小
        )
        
        self.setFixedSize(400, 300)  # 固定尺寸
```

### 设置面板（可调整大小，不可拖拽）

```python
class SettingsPanel(QWidget):
    def __init__(self):
        super().__init__()
        
        # 只启用调整大小（适合停靠的面板）
        self.helper = FramelessHelper(
            self,
            enable_drag=False,
            enable_resize=True,
            margin=12  # 更宽的边缘，更容易抓取
        )
        
        self.setMinimumSize(300, 400)
```

## 🔍 常见问题

### Q: 为什么我的按钮点击不了？
**A:** 确保 Helper 的 `eventFilter` 返回 `False`，这样事件会继续传递给子控件。我们的实现已经正确处理了这个问题。

### Q: 如何临时禁用拖拽？
```python
self.helper.set_draggable(False)  # 禁用
# ... 做一些事情 ...
self.helper.set_draggable(True)   # 恢复
```

### Q: 如何改变边缘检测区域的大小？
```python
self.helper.set_margin(12)  # 从 8px 改为 12px
```

### Q: 调整大小时窗口闪烁怎么办？
```python
# 设置合理的最小/最大尺寸
self.setMinimumSize(300, 400)
self.setMaximumSize(1920, 1080)
```

## 📊 与 Mixin 模式对比

| 特性 | Helper 模式 | Mixin 模式 |
|-----|------------|-----------|
| 代码行数 | 1 行 | 5+ 行 |
| 继承结构 | 不改变 | 需要多重继承 |
| 动态控制 | ✅ 支持 | ❌ 困难 |
| 事件冲突 | ✅ 不会冲突 | ⚠️ 可能冲突 |
| 子控件事件 | ✅ 正常工作 | ⚠️ 需要小心处理 |
| 调试难度 | ✅ 简单 | ⚠️ 复杂 |
| 工业推荐 | ✅ 推荐 | ⚠️ 不推荐 |

## 🚀 最佳实践

1. **始终设置最小尺寸**
   ```python
   self.setMinimumSize(300, 400)  # 防止窗口缩得太小
   ```

2. **根据需求选择功能**
   ```python
   # 普通窗口：两者都启用
   enable_drag=True, enable_resize=True
   
   # 固定大小对话框：只启用拖拽
   enable_drag=True, enable_resize=False
   
   # 停靠面板：只启用调整大小
   enable_drag=False, enable_resize=True
   ```

3. **合理设置边缘区域**
   ```python
   margin=8   # 标准（易用性适中）
   margin=12  # 更宽（更容易抓取边缘）
   margin=5   # 更窄（更多拖拽区域）
   ```

4. **保存 Helper 引用**
   ```python
   # ✅ 正确 - 作为实例变量
   self.helper = FramelessHelper(self)
   
   # ❌ 错误 - 局部变量会被垃圾回收
   helper = FramelessHelper(self)
   ```
