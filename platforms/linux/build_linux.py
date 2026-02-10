"""
Linux 打包脚本

生成 .AppImage 便携应用
使用 PyInstaller + appimage-builder (或 AppImageTool)
"""
import os
import sys
import subprocess
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from build_config import get_platform_config, APP_NAME, APP_VERSION, APP_DESCRIPTION

def build_linux():
    """构建 Linux 应用"""
    print("🔨 开始构建 Linux 应用...")
    
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
        print("✅ Linux 构建成功!")
        dist_path = main_py.parent / "dist" / config['name']
        print(f"📁 输出目录: {dist_path}")
        
        # 可选: 创建 AppImage
        create_appimage_choice = input("\n是否创建 AppImage? [y/N]: ")
        if create_appimage_choice.lower() == 'y':
            create_appimage(dist_path)
    else:
        print("❌ 构建失败!")
        sys.exit(1)


def create_appimage(dist_path):
    """创建 AppImage"""
    print("🔨 创建 AppImage...")
    
    appdir = dist_path.parent / f"{APP_NAME}.AppDir"
    
    # 创建 AppDir 结构
    print("📁 创建 AppDir 结构...")
    appdir.mkdir(exist_ok=True)
    (appdir / "usr" / "bin").mkdir(parents=True, exist_ok=True)
    (appdir / "usr" / "share" / "applications").mkdir(parents=True, exist_ok=True)
    (appdir / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps").mkdir(parents=True, exist_ok=True)
    
    # 复制可执行文件
    import shutil
    shutil.copytree(dist_path, appdir / "usr" / "bin" / APP_NAME, dirs_exist_ok=True)
    
    # 创建 .desktop 文件
    desktop_content = f"""[Desktop Entry]
Type=Application
Name={APP_NAME}
Comment={APP_DESCRIPTION}
Exec={APP_NAME}
Icon={APP_NAME}
Categories=Game;Utility;
Terminal=false
"""
    desktop_file = appdir / f"{APP_NAME}.desktop"
    desktop_file.write_text(desktop_content)
    
    # 复制图标
    icon_src = Path(__file__).parent.parent.parent / "assets" / "icon" / "app_icon.png"
    if icon_src.exists():
        icon_dst = appdir / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps" / f"{APP_NAME}.png"
        shutil.copy2(icon_src, icon_dst)
        # 顶层图标链接
        (appdir / f"{APP_NAME}.png").symlink_to(icon_dst)
    
    # AppRun 脚本
    apprun_content = f"""#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${{SELF%/*}}
export PATH="${{HERE}}/usr/bin:${{PATH}}"
export LD_LIBRARY_PATH="${{HERE}}/usr/lib:${{LD_LIBRARY_PATH}}"
exec "${{HERE}}/usr/bin/{APP_NAME}/{APP_NAME}" "$@"
"""
    apprun_file = appdir / "AppRun"
    apprun_file.write_text(apprun_content)
    apprun_file.chmod(0o755)
    
    # 使用 appimagetool 构建
    print("📦 使用 appimagetool 构建 AppImage...")
    
    # 下载 appimagetool (如果不存在)
    appimagetool = Path.home() / ".local" / "bin" / "appimagetool"
    if not appimagetool.exists():
        print("下载 appimagetool...")
        appimagetool.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            "wget",
            "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage",
            "-O", str(appimagetool)
        ])
        appimagetool.chmod(0o755)
    
    # 构建 AppImage
    appimage_name = f"{APP_NAME}-{APP_VERSION}-x86_64.AppImage"
    result = subprocess.run([
        str(appimagetool),
        str(appdir),
        str(dist_path.parent / appimage_name)
    ])
    
    if result.returncode == 0:
        print(f"✅ AppImage 创建成功: {appimage_name}")
    else:
        print("⚠️  AppImage 创建失败")


if __name__ == "__main__":
    if not sys.platform.startswith("linux"):
        print("⚠️  此脚本仅在 Linux 上运行")
        print("💡 当前平台:", sys.platform)
        sys.exit(1)
    
    build_linux()
