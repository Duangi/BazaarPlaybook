#!/usr/bin/env python3
"""
Linux/Steam Deck 窗口管理测试脚本

测试 X11/EWMH 窗口管理功能是否正常工作
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loguru import logger

# 配置日志
logger.remove()
logger.add(sys.stdout, level="INFO")


def check_x11_environment():
    """检查 X11 环境"""
    logger.info("=" * 60)
    logger.info("检查 X11 环境")
    logger.info("=" * 60)
    
    # 检查 DISPLAY 变量
    display = os.environ.get('DISPLAY')
    if display:
        logger.success(f"✅ DISPLAY 环境变量: {display}")
    else:
        logger.error("❌ DISPLAY 环境变量未设置（可能不在 X11 环境）")
        return False
    
    # 检查会话类型
    session_type = os.environ.get('XDG_SESSION_TYPE')
    if session_type:
        logger.info(f"会话类型: {session_type}")
        if session_type == 'x11':
            logger.success("✅ 运行在原生 X11 会话")
        elif session_type == 'wayland':
            logger.warning("⚠️  运行在 Wayland，将使用 XWayland 兼容层")
    
    # 尝试测试 X11 连接
    try:
        import subprocess
        result = subprocess.run(['xdpyinfo'], capture_output=True, timeout=2)
        if result.returncode == 0:
            logger.success("✅ X11 显示服务器连接正常")
            # 提取屏幕信息
            output = result.stdout.decode('utf-8')
            for line in output.split('\n')[:10]:
                if 'dimensions' in line or 'resolution' in line:
                    logger.info(f"  {line.strip()}")
            return True
        else:
            logger.error("❌ 无法连接到 X11 显示服务器")
            return False
    except Exception as e:
        logger.warning(f"⚠️  无法运行 xdpyinfo: {e}")
        return True  # 继续尝试


def test_linux_imports():
    """测试 Linux 依赖导入"""
    logger.info("\n" + "=" * 60)
    logger.info("测试依赖库")
    logger.info("=" * 60)
    
    all_ok = True
    
    # 测试 Xlib
    try:
        from Xlib import display, X
        logger.success("✅ python-xlib 已安装")
    except ImportError as e:
        logger.error(f"❌ python-xlib 未安装: {e}")
        logger.info("   安装命令: pip install python-xlib")
        all_ok = False
    
    # 测试 ewmh
    try:
        import ewmh
        logger.success("✅ ewmh 已安装")
    except ImportError as e:
        logger.error(f"❌ ewmh 未安装: {e}")
        logger.info("   安装命令: pip install ewmh")
        all_ok = False
    
    return all_ok


def test_window_manager():
    """测试窗口管理器"""
    logger.info("\n" + "=" * 60)
    logger.info("测试窗口管理器")
    logger.info("=" * 60)
    
    try:
        from platforms.linux.window import LinuxWindowManager
        
        manager = LinuxWindowManager()
        logger.success(f"✅ LinuxWindowManager 初始化成功")
        
        # 测试获取前台窗口
        title = manager.get_foreground_window_title()
        if title:
            logger.success(f"✅ 前台窗口标题: {title}")
        else:
            logger.warning("⚠️  无法获取前台窗口标题")
        
        # 测试窗口矩形（如果有前台窗口）
        if title:
            rect = manager.get_window_rect(title, exact_match=True)
            if rect:
                x, y, w, h = rect
                logger.success(f"✅ 窗口矩形: x={x}, y={y}, width={w}, height={h}")
            else:
                logger.warning(f"⚠️  无法获取窗口 '{title}' 的矩形")
        
        # 测试焦点检测
        is_valid = manager.is_focus_valid("Test")
        logger.info(f"焦点有效性测试: {is_valid}")
        
        # 测试鼠标位置
        if title:
            rect = manager.get_window_rect(title, exact_match=True)
            if rect:
                x, y, w, h = rect
                rel_x, rel_y = manager.get_mouse_pos_relative(x, y)
                logger.info(f"相对鼠标位置: ({rel_x}, {rel_y})")
        
        return True
        
    except Exception as e:
        logger.exception(f"❌ 窗口管理器测试失败: {e}")
        return False


def test_adapter():
    """测试适配器"""
    logger.info("\n" + "=" * 60)
    logger.info("测试平台适配器")
    logger.info("=" * 60)
    
    try:
        from platforms.adapter import PlatformAdapter
        
        manager = PlatformAdapter.get_window_manager()
        logger.success(f"✅ 适配器返回: {type(manager).__name__}")
        
        # 测试统一接口
        from utils.window_utils import (
            get_foreground_window_title,
            get_window_rect,
            is_focus_valid
        )
        
        title = get_foreground_window_title()
        logger.success(f"✅ 通过 utils 获取前台窗口: {title}")
        
        if title:
            rect = get_window_rect(title)
            if rect:
                logger.success(f"✅ 通过 utils 获取窗口矩形: {rect}")
        
        return True
        
    except Exception as e:
        logger.exception(f"❌ 适配器测试失败: {e}")
        return False


def test_steam_deck_specific():
    """Steam Deck 特定测试"""
    logger.info("\n" + "=" * 60)
    logger.info("Steam Deck 特定检查")
    logger.info("=" * 60)
    
    # 检查是否为 Steam Deck
    try:
        with open('/sys/devices/virtual/dmi/id/product_name', 'r') as f:
            product = f.read().strip()
            if 'Jupiter' in product or 'Galileo' in product:
                logger.success(f"✅ 检测到 Steam Deck: {product}")
            else:
                logger.info(f"设备型号: {product}")
    except:
        logger.info("非 Steam Deck 设备或无法读取设备信息")
    
    # 检查 Gamescope
    gamescope = os.environ.get('GAMESCOPE_WINDOW_ID')
    if gamescope:
        logger.success(f"✅ 检测到 Gamescope (游戏模式): Window ID {gamescope}")
    else:
        logger.info("未检测到 Gamescope（可能在桌面模式）")
    
    # 检查 Steam 运行时
    steam_runtime = os.environ.get('STEAM_RUNTIME')
    if steam_runtime:
        logger.info(f"Steam Runtime: {steam_runtime}")


def main():
    """主测试流程"""
    logger.info("🐧 Linux/Steam Deck 窗口管理测试\n")
    
    # 1. 检查环境
    if not check_x11_environment():
        logger.error("\n❌ X11 环境检查失败，某些功能可能不可用")
    
    # 2. 检查依赖
    if not test_linux_imports():
        logger.error("\n❌ 依赖库缺失，请先安装：")
        logger.error("   pip install python-xlib ewmh")
        sys.exit(1)
    
    # 3. 测试窗口管理器
    if not test_window_manager():
        logger.error("\n❌ 窗口管理器测试失败")
        sys.exit(1)
    
    # 4. 测试适配器
    if not test_adapter():
        logger.error("\n❌ 适配器测试失败")
        sys.exit(1)
    
    # 5. Steam Deck 特定检查
    test_steam_deck_specific()
    
    # 总结
    logger.info("\n" + "=" * 60)
    logger.success("🎉 所有测试通过！")
    logger.success("Linux 窗口管理功能已就绪")
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"\n测试过程中发生错误: {e}")
        sys.exit(1)
