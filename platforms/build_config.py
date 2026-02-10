"""
跨平台打包配置

支持将应用打包为:
- Windows: .exe (PyInstaller)
- macOS: .app / .dmg (PyInstaller + create-dmg)
- Linux: .AppImage (PyInstaller + appimage-builder)
"""
import sys
import platform

# 应用信息
APP_NAME = "BazaarPlaybook"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Duangi"
APP_DESCRIPTION = "Bazar游戏辅助工具"
APP_ICON = "../assets/icon/app_icon"  # 不含扩展名

# PyInstaller 通用配置
PYINSTALLER_CONFIG = {
    "name": APP_NAME,
    "console": False,  # 不显示控制台窗口
    "onefile": False,  # 使用 onedir 模式，更快且支持ONNX
    "windowed": True,  # GUI 应用
    "icon": None,  # 根据平台自动设置
    "datas": [
        ("../assets", "assets"),  # 资源文件
        ("../user_data", "user_data"),  # 用户数据
    ],
    "hiddenimports": [
        "PySide6",
        "onnxruntime",
        "rapidocr_onnxruntime",
        "cv2",
        "PIL",
        "loguru",
    ],
    "excludes": [
        "tkinter",
        "matplotlib",
        "pandas",
        "scipy",
        "jupyter",
    ],
}

# 平台特定配置
def get_platform_config():
    """获取当前平台的打包配置"""
    config = PYINSTALLER_CONFIG.copy()
    
    if sys.platform == "win32":
        # Windows 配置
        config["icon"] = f"{APP_ICON}.ico"
        config["hiddenimports"].extend([
            "dxcam",
            "keyboard",
            "mouse",
            "pywin32",
        ])
        
    elif sys.platform == "darwin":
        # macOS 配置
        config["icon"] = f"{APP_ICON}.icns"
        config["hiddenimports"].extend([
            "AppKit",
            "Cocoa",
            "Quartz",
            "ApplicationServices",
            "objc",
        ])
        # macOS 需要的额外选项
        config["osx_bundle_identifier"] = f"com.{APP_AUTHOR.lower()}.{APP_NAME.lower()}"
        config["codesign_identity"] = None  # 如果有开发者证书，填写证书名称
        
    elif sys.platform.startswith("linux"):
        # Linux 配置
        config["icon"] = f"{APP_ICON}.png"
        config["hiddenimports"].extend([
            "python-xlib",
            "ewmh",
        ])
    
    return config


# macOS 权限配置 (Info.plist)
MACOS_PLIST_ADDITIONS = """
<key>NSAppleEventsUsageDescription</key>
<string>需要控制其他应用以提供覆盖功能</string>
<key>NSAccessibilityUsageDescription</key>
<string>需要辅助功能权限以实现窗口置顶</string>
<key>NSCameraUsageDescription</key>
<string>需要屏幕捕获权限以识别游戏内容</string>
<key>NSScreenCaptureDescription</key>
<string>需要屏幕录制权限以捕获游戏画面</string>
"""
