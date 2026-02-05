# 窗口功能 Mixin 使用指南

## 📚 概述

`gui/windows/base.py` 提供了两个独立的 Mixin 类，可以为任何 QWidget 添加功能：

- **DraggableMixin**: 可拖拽功能（支持顶部吸附）
- **ResizableMixin**: 可调整大小功能（边缘拖拽）

## 🎯 为什么使用 Mixin？

**传统继承的问题：**
```python
# ❌ 只能选择一个基类
class MyWindow(DraggableWindow):  # 只有拖拽功能
    pass
```

**Mixin 的优势：**
```python
# ✅ 灵活组合多个功能
class MyWindow(QWidget, DraggableMixin, ResizableMixin):
    pass
```

## 📖 使用方法

### 1️⃣ 基础用法 - 只需要拖拽

```python
from PySide6.QtWidgets import QWidget
from gui.windows.base import DraggableMixin

class MyWindow(QWidget, DraggableMixin):
    def __init__(self):
        super().__init__()
        
        # 启用拖拽功能
        self.setup_draggable(snap_to_top=True)  # 启用顶部吸附
        # 或
        self.setup_draggable(snap_to_top=False)  # 禁用顶部吸附
```

### 2️⃣ 进阶用法 - 拖拽 + 调整大小

```python
from PySide6.QtWidgets import QWidget
from gui.windows.base import DraggableMixin, ResizableMixin

class MyWindow(QWidget, DraggableMixin, ResizableMixin):
    def __init__(self):
        super().__init__()
        
        # 启用拖拽功能
        self.setup_draggable(snap_to_top=True)
        
        # 启用调整大小功能
        self.setup_resizable(
            min_width=400,      # 最小宽度
            min_height=300,     # 最小高度
            max_width=1200,     # 最大宽度
            max_height=900,     # 最大高度
            resize_margin=8     # 边缘检测区域（像素）
        )
```

### 3️⃣ 高级用法 - 只需要调整大小

```python
from PySide6.QtWidgets import QWidget
from gui.windows.base import ResizableMixin

class MyWindow(QWidget, ResizableMixin):
    def __init__(self):
        super().__init__()
        
        # 只启用调整大小，不可拖拽
        self.setup_resizable(
            min_width=300,
            min_height=200,
            resize_margin=10  # 更宽的边缘检测区域
        )
```

## 🔧 完整示例

```python
import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from gui.windows.base import DraggableMixin, ResizableMixin

class CustomWindow(QWidget, DraggableMixin, ResizableMixin):
    def __init__(self):
        super().__init__()
        
        # 设置窗口属性
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # ✅ 启用拖拽功能
        self.setup_draggable(snap_to_top=True)
        
        # ✅ 启用调整大小功能
        self.setup_resizable(
            min_width=400,
            min_height=300,
            max_width=1000,
            max_height=800,
            resize_margin=8
        )
        
        # 设置UI
        layout = QVBoxLayout(self)
        label = QLabel("拖动我 or 调整大小！")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        self.resize(500, 400)
        self.setStyleSheet("""
            QWidget {
                background: #2a2a2a;
                border: 2px solid #ffcc00;
                border-radius: 12px;
            }
            QLabel {
                color: white;
                font-size: 20px;
            }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CustomWindow()
    window.show()
    sys.exit(app.exec())
```

## 🎨 功能特性

### DraggableMixin 特性

- ✅ 全窗口拖拽（点击任意位置）
- ✅ 可选的顶部吸附（拖到顶部自动吸附到 y=0）
- ✅ 与 ResizableMixin 兼容（拖拽时不会触发调整大小）

### ResizableMixin 特性

- ✅ 八个方向调整大小：
  - 边缘：上、下、左、右
  - 角落：左上、右上、左下、右下
- ✅ 智能光标变化（靠近边缘时自动显示调整光标）
- ✅ 尺寸限制（min/max width/height）
- ✅ 可配置的边缘检测区域
- ✅ 与 DraggableMixin 兼容（调整大小时不会触发拖拽）

## 🔄 向后兼容

如果你的代码仍在使用旧的 `DraggableWindow` 基类，它仍然可以工作：

```python
from gui.windows.base import DraggableWindow

class OldStyleWindow(DraggableWindow):
    def __init__(self):
        super().__init__(snap_to_top=True)
        # ... 你的代码
```

但推荐迁移到 Mixin 方式以获得更多灵活性！

## 💡 注意事项

1. **继承顺序很重要！** 始终将 `QWidget` 放在最前面：
   ```python
   # ✅ 正确
   class MyWindow(QWidget, DraggableMixin, ResizableMixin):
       pass
   
   # ❌ 错误
   class MyWindow(DraggableMixin, QWidget):  # 不要这样做！
       pass
   ```

2. **必须调用 setup 方法！** Mixin 不会自动启用功能：
   ```python
   def __init__(self):
       super().__init__()
       self.setup_draggable()    # ✅ 记得调用
       self.setup_resizable()     # ✅ 记得调用
   ```

3. **调整大小时需要使用 `resize()` 而不是 `setFixedSize()`：**
   ```python
   # ✅ 正确 - 允许用户调整大小
   self.resize(500, 400)
   
   # ❌ 错误 - 锁定大小，用户无法调整
   self.setFixedSize(500, 400)
   ```

## 🎯 实际应用示例

**Sidebar 窗口（拖拽 + 调整大小）：**
```python
class SidebarWindow(QWidget, DraggableMixin, ResizableMixin):
    def __init__(self):
        super().__init__()
        self.setup_draggable(snap_to_top=True)
        self.setup_resizable(min_width=400, min_height=500)
```

**浮动提示窗口（只能拖拽，固定大小）：**
```python
class TooltipWindow(QWidget, DraggableMixin):
    def __init__(self):
        super().__init__()
        self.setup_draggable(snap_to_top=False)
        self.setFixedSize(300, 100)  # 固定大小
```

**设置对话框（可调整大小，不可拖拽）：**
```python
class SettingsDialog(QDialog, ResizableMixin):
    def __init__(self):
        super().__init__()
        self.setup_resizable(min_width=600, min_height=400)
        # 不调用 setup_draggable，所以不可拖拽
```
