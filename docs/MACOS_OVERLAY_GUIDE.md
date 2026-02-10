# macOS 全屏覆盖功能指南

## 功能概述

从 Tauri 迁移到 PySide6 后，我们通过 PyObjC 实现了 macOS 全屏应用覆盖功能，允许应用窗口显示在全屏游戏之上。

## 技术实现

### 核心原理

**Windows/Linux:**
- 使用 Qt 标准的 `WindowStaysOnTopHint` 标志
- 窗口管理器自动处理层级

**macOS:**
- Qt 的 `WindowStaysOnTopHint` **无法覆盖全屏应用**
- 需要通过 `NSWindow` API 设置特殊属性：
  - `NSFloatingWindowLevel (3)`: 窗口层级设为浮动
  - `NSWindowCollectionBehaviorCanJoinAllSpaces`: 出现在所有空间
  - `NSWindowCollectionBehaviorFullScreenAuxiliary`: 允许在全屏应用中显示

### 从 Tauri 迁移

**之前 (Tauri/Rust):**
```rust
use tauri::window::NSPanel;

NSPanel::window()
    .set_level(NSFloatingWindowLevel)
    .set_collection_behavior(NSWindowCollectionBehaviorCanJoinAllSpaces)
```

**现在 (PySide6/Python):**
```python
from utils.overlay_helper import enable_overlay_mode

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        enable_overlay_mode(self)  # 一行代码搞定！
```

## 使用方法

### 1. 导入覆盖助手

```python
from utils.overlay_helper import enable_overlay_mode
```

### 2. 在窗口初始化时调用

```python
class GameOverlay(QWidget):
    def __init__(self):
        super().__init__()
        
        # 启用覆盖模式（自动处理跨平台差异）
        enable_overlay_mode(
            self,
            frameless=True,      # 无边框窗口
            translucent=True     # 透明背景
        )
        
        # ... 其他初始化代码
```

### 3. 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `widget` | QWidget | 必需 | 要启用覆盖的窗口对象 |
| `frameless` | bool | True | 是否无边框 |
| `translucent` | bool | True | 是否透明背景 |

### 4. 高级功能

```python
from utils.overlay_helper import (
    enable_overlay_mode,
    enable_click_through,   # 启用点击穿透
    disable_click_through   # 禁用点击穿透
)

# 创建不接收鼠标事件的覆盖（仅显示信息）
widget = QWidget()
enable_overlay_mode(widget)
enable_click_through(widget)  # 鼠标点击穿透到游戏
```

## 已集成窗口

以下窗口已自动启用 macOS 全屏覆盖支持：

- ✅ `SidebarWindow` - 侧边栏主窗口
- ✅ `IslandWindow` - 灵动岛窗口
- ✅ `DebugOverlayWindow` - 调试信息窗口
- ✅ `DiagnosticsWindow` - 诊断窗口
- ✅ `StartWindow` - 启动窗口
- ✅ `SettingsDialog` - 设置对话框

无需修改任何代码，这些窗口在 macOS 上会自动支持全屏游戏覆盖。

## 系统要求

### macOS 依赖

```bash
# 已包含在 requirements.txt 中
pip install pyobjc-core
pip install pyobjc-framework-Cocoa
pip install pyobjc-framework-Quartz
```

### 权限设置

在 **macOS Sequoia (15.0+)** 上，需要授予辅助功能权限：

1. 打开 **系统设置** > **隐私与安全性** > **辅助功能**
2. 添加 Python 或应用程序
3. 重启应用

## 测试验证

### 快速测试

```bash
# 运行集成测试
python test_overlay_integration.py

# 运行 macOS 覆盖演示
python test_macos_overlay.py
```

### 完整测试流程

1. **启动全屏游戏** (The Bazaar)
2. **运行应用**
3. **验证覆盖效果**:
   - 窗口应该显示在游戏之上
   - 可以与窗口交互
   - 切换空间时窗口跟随

## 故障排除

### 窗口不显示在全屏游戏上

**可能原因:**
- PyObjC 未安装
- macOS 版本过旧 (需要 10.9+)
- 辅助功能权限未授予

**解决方法:**
```bash
# 检查 PyObjC 安装
python -c "from AppKit import NSWindow; print('✅ PyObjC 已安装')"

# 重新安装依赖
pip install --upgrade pyobjc-core pyobjc-framework-Cocoa
```

### 日志检查

启用调试日志查看详细信息：

```python
from loguru import logger

logger.enable("utils.overlay_helper")
```

查找以下日志消息：
- ✅ `macOS 全屏覆盖已启用` - 成功
- ⚠️ `macOS 覆盖功能不可用` - PyObjC 缺失
- ❌ `macOS 全屏覆盖设置失败` - 运行时错误

## 性能影响

- **Windows/Linux**: 无额外开销（Qt 原生支持）
- **macOS**: 轻微开销（~1ms，仅在窗口显示时）

## 实现细节

### 关键代码路径

```
utils/overlay_helper.py              # 主要实现
└── enable_overlay_mode()           # 公共接口
    ├── 设置 Qt 窗口标志（所有平台）
    └── _setup_macos_fullscreen_overlay()  # macOS 专用
        ├── 获取 NSWindow 对象
        ├── 设置窗口层级 (NSFloatingWindowLevel)
        └── 设置集合行为 (CanJoinAllSpaces | FullScreenAuxiliary)
```

### NSWindow 层级说明

macOS 窗口层级（从低到高）：

| 层级 | 值 | 说明 |
|------|-----|------|
| NSNormalWindowLevel | 0 | 普通窗口 |
| **NSFloatingWindowLevel** | **3** | **浮动窗口（我们使用）** |
| NSTornOffMenuWindowLevel | 5 | 分离菜单 |
| NSModalPanelWindowLevel | 8 | 模态面板 |
| NSMainMenuWindowLevel | 24 | 主菜单 |
| NSStatusWindowLevel | 25 | 状态栏 |
| NSPopUpMenuWindowLevel | 101 | 弹出菜单 |
| NSScreenSaverWindowLevel | 1000 | 屏幕保护 |

使用 `NSFloatingWindowLevel` 确保窗口在普通窗口之上，但不会干扰系统 UI。

## 相关文档

- [WINDOW_MANAGER_REFACTOR.md](WINDOW_MANAGER_REFACTOR.md) - 跨平台窗口管理
- [PyObjC 官方文档](https://pyobjc.readthedocs.io/)
- [NSWindow 参考](https://developer.apple.com/documentation/appkit/nswindow)

## 更新日志

**2024-01-XX:**
- ✅ 从 Tauri NSPanel 迁移到 PySide6 + PyObjC
- ✅ 创建 `overlay_helper.py` 统一接口
- ✅ 集成到 6 个现有窗口
- ✅ 添加测试脚本和文档
