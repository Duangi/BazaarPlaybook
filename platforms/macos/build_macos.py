"""
macOS 打包脚本

生成 .app 应用包和 .dmg 安装镜像
使用 PyInstaller + create-dmg
"""
import os
import sys
import subprocess
import plistlib
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from build_config import (
    get_platform_config, 
    APP_NAME, 
    APP_VERSION, 
    APP_DESCRIPTION,
    MACOS_PLIST_ADDITIONS
)

def build_macos():
    """构建 macOS 应用"""
    print("🔨 开始构建 macOS 应用...")
    
    config = get_platform_config()
    
    # 构建 PyInstaller 命令
    cmd = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        f"--name={config['name']}",
    ]
    
    if config.get("console") is False:
        cmd.append("--noconsole")
    
    if config.get("onefile"):
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")
    
    if config.get("windowed"):
        cmd.append("--windowed")
    
    if config.get("icon"):
        icon_path = Path(__file__).parent.parent.parent / config["icon"]
        if icon_path.exists():
            cmd.append(f"--icon={icon_path}")
    
    # macOS 特定选项
    if config.get("osx_bundle_identifier"):
        cmd.append(f"--osx-bundle-identifier={config['osx_bundle_identifier']}")
    
    # 添加数据文件
    for src, dst in config.get("datas", []):
        src_path = Path(__file__).parent.parent.parent / src
        if src_path.exists():
            cmd.append(f"--add-data={src_path}:{dst}")
    
    # 添加隐藏导入
    for imp in config.get("hiddenimports", []):
        cmd.append(f"--hidden-import={imp}")
    
    # 排除模块
    for exc in config.get("excludes", []):
        cmd.append(f"--exclude-module={exc}")
    
    # 主文件
    main_py = Path(__file__).parent.parent.parent / "main.py"
    cmd.append(str(main_py))
    
    print(f"📦 执行命令: {' '.join(cmd)}")
    
    # 执行构建
    result = subprocess.run(cmd, cwd=str(main_py.parent))
    
    if result.returncode == 0:
        print("✅ macOS 构建成功!")
        app_path = main_py.parent / "dist" / f"{config['name']}.app"
        print(f"📁 应用路径: {app_path}")
        
        # 修改 Info.plist 添加权限说明
        patch_info_plist(app_path)
        
        # 可选: 创建 DMG
        create_dmg_choice = input("\n是否创建 .dmg 安装镜像? [y/N]: ")
        if create_dmg_choice.lower() == 'y':
            create_dmg(app_path)
    else:
        print("❌ 构建失败!")
        sys.exit(1)


def patch_info_plist(app_path):
    """修改 Info.plist 添加权限说明"""
    plist_path = app_path / "Contents" / "Info.plist"
    
    if not plist_path.exists():
        print("⚠️  找不到 Info.plist")
        return
    
    print("📝 添加权限说明到 Info.plist...")
    
    try:
        with open(plist_path, 'rb') as f:
            plist = plistlib.load(f)
        
        # 添加权限说明
        plist['NSAppleEventsUsageDescription'] = "需要控制其他应用以提供覆盖功能"
        plist['NSAccessibilityUsageDescription'] = "需要辅助功能权限以实现窗口置顶"
        plist['NSScreenCaptureDescription'] = "需要屏幕录制权限以捕获游戏画面"
        
        with open(plist_path, 'wb') as f:
            plistlib.dump(plist, f)
        
        print("✅ Info.plist 更新成功")
    except Exception as e:
        print(f"⚠️  更新 Info.plist 失败: {e}")


def create_dmg(app_path):
    """创建 DMG 安装镜像"""
    print("🔨 创建 DMG 镜像...")
    
    # 检查是否安装了 create-dmg
    try:
        subprocess.run(["create-dmg", "--version"], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE,
                      check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  未找到 create-dmg，尝试安装...")
        print("💡 运行: brew install create-dmg")
        install = input("是否现在安装? [y/N]: ")
        if install.lower() == 'y':
            subprocess.run(["brew", "install", "create-dmg"])
        else:
            print("跳过 DMG 创建")
            return
    
    dmg_name = f"{APP_NAME}-{APP_VERSION}-macOS.dmg"
    dmg_path = app_path.parent / dmg_name
    
    # 删除已存在的 DMG
    if dmg_path.exists():
        dmg_path.unlink()
    
    cmd = [
        "create-dmg",
        "--volname", APP_NAME,
        "--volicon", str(app_path / "Contents" / "Resources" / "icon-windowed.icns"),
        "--window-pos", "200", "120",
        "--window-size", "600", "400",
        "--icon-size", "100",
        "--icon", f"{APP_NAME}.app", "175", "120",
        "--hide-extension", f"{APP_NAME}.app",
        "--app-drop-link", "425", "120",
        str(dmg_path),
        str(app_path)
    ]
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print(f"✅ DMG 创建成功: {dmg_path}")
    else:
        print("⚠️  DMG 创建失败（可能是权限问题，可手动使用磁盘工具创建）")


if __name__ == "__main__":
    if sys.platform != "darwin":
        print("⚠️  此脚本仅在 macOS 上运行")
        print("💡 当前平台:", sys.platform)
        sys.exit(1)
    
    build_macos()
