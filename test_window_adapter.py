#!/usr/bin/env python3
"""
跨平台窗口管理测试脚本

演示如何使用适配器获取窗口信息（Windows/macOS 自动切换）
"""

import sys
from loguru import logger

# 配置日志
logger.remove()
logger.add(sys.stdout, level="INFO")

def test_window_manager():
    """测试窗口管理功能"""
    from utils.window_utils import (
        get_foreground_window_title,
        is_focus_valid,
        get_window_rect,
    )
    
    logger.info(f"当前平台: {sys.platform}")
    
    # 1. 获取当前前台窗口
    title = get_foreground_window_title()
    logger.info(f"前台窗口标题: {title}")
    
    # 2. 检查焦点是否有效
    is_valid = is_focus_valid("The Bazaar")
    logger.info(f"焦点是否有效（游戏或本应用）: {is_valid}")
    
    # 3. 尝试获取窗口矩形（如果有的话）
    if title:
        rect = get_window_rect(title, exact_match=True)
        if rect:
            x, y, w, h = rect
            logger.info(f"窗口矩形: x={x}, y={y}, width={w}, height={h}")
        else:
            logger.warning(f"无法获取窗口 '{title}' 的矩形")
    
    logger.success("✅ 窗口管理器测试完成")


def test_adapter_direct():
    """直接测试适配器"""
    from platforms.adapter import PlatformAdapter
    
    manager = PlatformAdapter.get_window_manager()
    logger.info(f"窗口管理器类型: {type(manager).__name__}")
    
    # 测试基本功能
    title = manager.get_foreground_window_title()
    logger.info(f"通过适配器获取的前台窗口: {title}")


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("开始测试跨平台窗口管理")
    logger.info("=" * 60)
    
    try:
        test_adapter_direct()
        print()
        test_window_manager()
    except Exception as e:
        logger.exception(f"测试失败: {e}")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.success("所有测试通过！")
