"""
macOS 全屏游戏覆盖支持

解决 macOS 上全屏应用遮挡 Qt 窗口的问题
"""
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from loguru import logger

if sys.platform == "darwin":
    try:
        # macOS 特定导入
        from AppKit import NSWindow, NSFloatingWindowLevel, NSWindowCollectionBehaviorCanJoinAllSpaces
        MACOS_AVAILABLE = True
    except ImportError:
        MACOS_AVAILABLE = False
        logger.warning("AppKit 不可用，macOS 全屏覆盖功能可能受限")
else:
    MACOS_AVAILABLE = False


def setup_macos_overlay(widget: QWidget):
    """
    配置 macOS 窗口以支持全屏游戏覆盖
    
    等价于 Tauri 的 NSPanel + visibleOnAllWorkspaces
    
    Args:
        widget: 需要设置的 Qt 窗口
    """
    if not MACOS_AVAILABLE or sys.platform != "darwin":
        return
    
    try:
        # 获取原生 NSWindow 对象
        window_id = widget.winId()
        if not window_id:
            logger.warning("无法获取窗口 ID")
            return
        
        # 通过 winId 获取 NSWindow
        from PyObjCTools import AppHelper
        import objc
        
        # 获取 NSWindow
        ns_window = objc.objc_object(c_void_p=int(window_id))
        
        # 设置窗口层级为浮动窗口级别（类似 NSPanel）
        # NSFloatingWindowLevel = 3，确保在大多数窗口之上
        ns_window.setLevel_(NSFloatingWindowLevel)
        
        # 设置窗口集合行为：可以加入所有空间（全屏游戏也能看到）
        # 等价于 Tauri 的 visibleOnAllWorkspaces
        collection_behavior = ns_window.collectionBehavior()
        collection_behavior |= NSWindowCollectionBehaviorCanJoinAllSpaces
        ns_window.setCollectionBehavior_(collection_behavior)
        
        logger.success("macOS 全屏覆盖已启用")
        
    except Exception as e:
        logger.error(f"macOS 全屏覆盖设置失败: {e}")


def setup_window_overlay(widget: QWidget):
    """
    跨平台窗口覆盖设置（统一接口）
    
    Args:
        widget: 需要设置的 Qt 窗口
    """
    # 基础 Qt 设置（所有平台）
    widget.setWindowFlags(
        Qt.FramelessWindowHint |
        Qt.WindowStaysOnTopHint |
        Qt.Tool
    )
    widget.setAttribute(Qt.WA_TranslucentBackground)
    
    # macOS 特殊处理
    if sys.platform == "darwin":
        # 需要先显示窗口才能获取 winId
        widget.show()
        setup_macos_overlay(widget)
