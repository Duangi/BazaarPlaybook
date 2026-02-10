"""
Windows 打包脚本

生成 .exe 可执行文件
使用 PyInstaller + Inno Setup (可选)
"""
import os
import sys
import subprocess
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from build_config import get_platform_config, APP_NAME, APP_VERSION

def build_windows():
    """构建 Windows 可执行文件"""
    print("🔨 开始构建 Windows 应用...")
    
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
            cmd.append(f"--add-data={src_path};{dst}")
    
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
        print("✅ Windows 构建成功!")
        dist_path = main_py.parent / "dist" / config['name']
        print(f"📁 输出目录: {dist_path}")
        
        # 可选: 创建安装程序
        create_installer = input("\n是否创建 Inno Setup 安装程序? (需要安装 Inno Setup) [y/N]: ")
        if create_installer.lower() == 'y':
            create_inno_installer(dist_path)
    else:
        print("❌ 构建失败!")
        sys.exit(1)


def create_inno_installer(dist_path):
    """创建 Inno Setup 安装程序"""
    print("🔨 创建安装程序...")
    # TODO: 生成 .iss 脚本并执行 ISCC
    print("⚠️  暂未实现，请手动使用 Inno Setup")


if __name__ == "__main__":
    if sys.platform != "win32":
        print("⚠️  此脚本仅在 Windows 上运行")
        print("💡 当前平台:", sys.platform)
        sys.exit(1)
    
    build_windows()
