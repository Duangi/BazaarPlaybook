# 跨平台打包指南

本目录包含了在 Windows、macOS 和 Linux 三个平台上打包应用的脚本。

## 📋 目录结构

```
platforms/
├── build_config.py          # 通用打包配置
├── windows/
│   └── build_windows.py     # Windows 打包脚本
├── macos/
│   └── build_macos.py       # macOS 打包脚本
└── linux/
    └── build_linux.py       # Linux 打包脚本
```

## 🛠️ 准备工作

### 1. 安装 PyInstaller

所有平台都需要安装 PyInstaller：

```bash
pip install pyinstaller
```

### 2. 平台特定依赖

#### Windows
- **可选**: [Inno Setup](https://jrsoftware.org/isinfo.php) - 创建安装程序

#### macOS
- **可选**: `create-dmg` - 创建 DMG 镜像
  ```bash
  brew install create-dmg
  ```

#### Linux
- **可选**: `appimagetool` - 创建 AppImage
  - 脚本会自动下载
  - 或手动: `wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage`

## 🚀 使用方法

### Windows 打包

在 Windows 上运行：

```bash
cd platforms/windows
python build_windows.py
```

输出文件：
- `dist/BazaarPlaybook/` - 应用目录（包含 .exe 和依赖）
- 可选: 安装程序（需要 Inno Setup）

### macOS 打包

在 macOS 上运行：

```bash
cd platforms/macos
python build_macos.py
```

输出文件：
- `dist/BazaarPlaybook.app` - macOS 应用包
- 可选: `BazaarPlaybook-1.0.0-macOS.dmg` - 安装镜像

#### macOS 权限配置

打包后的 `.app` 会自动添加以下权限说明：
- **辅助功能** (Accessibility) - 窗口置顶
- **屏幕录制** (Screen Capture) - 捕获游戏画面

用户首次运行时系统会提示授权。

### Linux 打包

在 Linux 上运行：

```bash
cd platforms/linux
python build_linux.py
```

输出文件：
- `dist/BazaarPlaybook/` - 应用目录
- 可选: `BazaarPlaybook-1.0.0-x86_64.AppImage` - 便携应用

## 📦 打包配置

所有配置在 `build_config.py` 中统一管理：

```python
# 修改应用信息
APP_NAME = "BazaarPlaybook"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Duangi"

# 添加/移除依赖
PYINSTALLER_CONFIG = {
    "hiddenimports": [...],  # 添加隐藏导入
    "excludes": [...],       # 排除不需要的模块
}
```

## 🎨 应用图标

图标文件位置：`assets/icon/`

需要准备以下格式：
- **Windows**: `app_icon.ico` (推荐 256x256)
- **macOS**: `app_icon.icns` (包含多种尺寸)
- **Linux**: `app_icon.png` (推荐 256x256)

### 创建 macOS .icns 文件

```bash
# 从 PNG 创建 iconset
mkdir app_icon.iconset
sips -z 16 16     icon.png --out app_icon.iconset/icon_16x16.png
sips -z 32 32     icon.png --out app_icon.iconset/icon_16x16@2x.png
sips -z 32 32     icon.png --out app_icon.iconset/icon_32x32.png
sips -z 64 64     icon.png --out app_icon.iconset/icon_32x32@2x.png
sips -z 128 128   icon.png --out app_icon.iconset/icon_128x128.png
sips -z 256 256   icon.png --out app_icon.iconset/icon_128x128@2x.png
sips -z 256 256   icon.png --out app_icon.iconset/icon_256x256.png
sips -z 512 512   icon.png --out app_icon.iconset/icon_256x256@2x.png
sips -z 512 512   icon.png --out app_icon.iconset/icon_512x512.png
sips -z 1024 1024 icon.png --out app_icon.iconset/icon_512x512@2x.png

# 生成 .icns
iconutil -c icns app_icon.iconset
```

## 🔧 常见问题

### 1. 打包后应用体积过大

- 检查 `excludes` 列表，排除不需要的模块（如 matplotlib, pandas）
- 使用 `--onedir` 而非 `--onefile`（后者会更大）

### 2. macOS 应用无法运行（安全提示）

```bash
# 移除隔离属性
xattr -cr BazaarPlaybook.app

# 或对应用签名（需要开发者证书）
codesign --force --deep --sign "Developer ID" BazaarPlaybook.app
```

### 3. Windows Defender 误报

- 首次运行可能被拦截
- 建议进行代码签名（需要证书）

### 4. ONNX 模型文件未打包

确保在 `build_config.py` 中添加：

```python
"datas": [
    ("../assets/models", "assets/models"),
]
```

## 📝 分发清单

打包完成后，分发以下文件：

### Windows
- `BazaarPlaybook.exe` + 依赖文件夹
- 或 `BazaarPlaybook-Setup.exe`（安装程序）

### macOS
- `BazaarPlaybook.dmg`（拖拽安装）
- 或 `BazaarPlaybook.app`（直接压缩）

### Linux
- `BazaarPlaybook-x86_64.AppImage`（便携）
- 或 `BazaarPlaybook-1.0.0.tar.gz`（源码）

## 🚀 快速测试

不打包直接运行 Python 脚本（**推荐开发时使用**）：

```bash
# 直接给 Python 解释器授权即可
# macOS: 系统设置 > 隐私与安全性 > 辅助功能
# 添加: /opt/miniconda3/envs/reborn/bin/python

# 运行
python main.py
```

打包主要用于：
- 分发给其他用户
- 不想安装 Python 环境
- 需要隐藏源代码
