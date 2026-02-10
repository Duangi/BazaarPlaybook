"""
Qt 窗口覆盖工具集

提供跨平台的窗口覆盖功能，特别优化 macOS 全屏游戏支持
"""
import sys
from ctypes import c_void_p
from PySide6.QtCore import Qt, QTimer, QEvent, QObject
from PySide6.QtWidgets import QWidget
from loguru import logger


def enable_overlay_mode(widget: QWidget, frameless: bool = True, translucent: bool = True):
    """
    启用窗口覆盖模式（跨平台）
    
    功能：
    - Windows: 使用 WindowStaysOnTopHint 保持最上层
    - macOS: 使用 NSFloatingWindowLevel 覆盖全屏应用
    - Linux: 使用 WindowStaysOnTopHint（X11 窗口管理器支持）
    
    Args:
        widget: Qt 窗口对象
        frameless: 是否无边框（默认 True）
        translucent: 是否启用透明背景（默认 True）
    
    示例:
        class MyOverlay(QWidget):
            def __init__(self):
                super().__init__()
                enable_overlay_mode(self)
    """
    # macOS：完全不同的处理方式，不使用 Qt 标志
    if sys.platform == "darwin":
        # 只设置最基础的标志
        flags = Qt.Window  # 普通窗口
        if frameless:
            flags |= Qt.FramelessWindowHint
        
        widget.setWindowFlags(flags)
        
        # 设置透明背景
        if translucent:
            widget.setAttribute(Qt.WA_TranslucentBackground)
        
        # 在窗口创建时立即设置原生属性（在 show 之前）
        widget.setAttribute(Qt.WA_NativeWindow, True)
        
        # 连接 show 事件，在窗口即将显示时立即应用原生设置
        original_show = widget.show
        
        def enhanced_show():
            """增强的 show 方法：显示前先设置原生层级"""
            # 先确保窗口句柄已创建
            widget.winId()  # 强制创建窗口
            
            # 立即应用原生设置
            apply_native_overlay_immediate(widget)
            
            # 调用原始 show
            original_show()
            
            # 再次确认（100ms 后）
            QTimer.singleShot(100, lambda: apply_native_overlay_immediate(widget))
        
        widget.show = enhanced_show
        
    else:
        # Windows/Linux: 使用标准 Qt 标志
        flags = Qt.WindowStaysOnTopHint | Qt.Tool
        widget.installEventFilter(helper)


def apply_native_overlay_immediate(widget: QWidget):
    """立即应用 macOS 原生覆盖（不等待事件）"""
    try:
        from AppKit import NSApp, NSWindow, NSView
        from Cocoa import (
            NSWindowCollectionBehaviorCanJoinAllSpaces,
            NSWindowCollectionBehaviorStationary,
            NSWindowCollectionBehaviorFullScreenAuxiliary,
            NSScreen,
        )
        import objc
        from ctypes import c_void_p
        
        window_id = widget.winId()
        ns_view = objc.objc_object(c_void_p=window_id)
        ns_window = ns_view.window()
        
        if ns_window:
            # 设置层级
            OVERLAY_LEVEL = 1000
            ns_window.setLevel_(OVERLAY_LEVEL)
            
            # 设置行为（在显示前设置）
            behavior = (NSWindowCollectionBehaviorCanJoinAllSpaces |
                       NSWindowCollectionBehaviorStationary |
                       NSWindowCollectionBehaviorFullScreenAuxiliary)
            ns_window.setCollectionBehavior_(behavior)
            
            # 强制前置到当前空间
            ns_window.orderFrontRegardless()
            ns_window.makeKeyAndOrderFront_(None)
            
            logger.debug(f"✅ 原生覆盖已应用: {widget.windowTitle() or widget.__class__.__name__} (层级: {ns_window.level()})")
    except Exception as e:
        logger.debug(f"原生覆盖失败: {e}")


def _setup_macos_fullscreen_overlay(widget: QWidget, silent: bool = False):
    """
    macOS 全屏覆盖内部实现
    
    使用 NSWindow API 设置窗口层级和集合行为
    等价于 Tauri 的 NSPanel + visibleOnAllWorkspaces
    
    Args:
        widget: Qt 窗口对象
        silent: 是否静默模式（不输出重复日志）
    """
    if sys.platform != "darwin":
        return
    
    try:
        # 尝试导入 macOS 框架
        from AppKit import NSApp, NSWindow, NSView
        from Cocoa import (
            NSFloatingWindowLevel,
            NSStatusWindowLevel,
            NSWindowCollectionBehaviorCanJoinAllSpaces,
            NSWindowCollectionBehaviorStationary,
            NSWindowCollectionBehaviorFullScreenAuxiliary,
            NSWindowCollectionBehaviorMoveToActiveSpace
        )
        from ApplicationServices import AXIsProcessTrusted
        import objc
        
        # 检查辅助功能权限
        if not AXIsProcessTrusted():
            if not silent:
                logger.warning("⚠️  macOS 覆盖功能需要辅助功能权限")
                logger.warning("请前往: 系统设置 > 隐私与安全性 > 辅助功能")
                logger.warning(f"添加: {sys.executable} (Python)")
                logger.warning("然后重启应用")
        
        # 获取窗口 ID (这是 NSView 的指针)
        window_id = widget.winId()
        
        # 将 Qt 的 WinId 转换为 NSView 对象
        # winId() 返回的是 NSView 的指针地址
        ns_view = objc.objc_object(c_void_p=window_id)
        
        # 从 NSView 获取其所属的 NSWindow
        ns_window = ns_view.window()
        
        if not ns_window:
            if not silent:
                logger.error(f"macOS: 无法从 Qt 窗口获取 NSWindow 对象")
            return
        
        # 设置窗口层级
        # macOS 窗口层级参考:
        # NSNormalWindowLevel = 0
        # NSFloatingWindowLevel = 3
        # NSStatusWindowLevel = 25
        # NSPopUpMenuWindowLevel = 101
        # NSScreenSaverWindowLevel = 1000
        # 
        # 使用自定义高层级，确保在几乎所有窗口之上
        # 但不要太高以免遮挡系统关键UI
        OVERLAY_LEVEL = 1000  # 等同于屏保层级
        ns_window.setLevel_(OVERLAY_LEVEL)
        
        # 强制窗口前置（忽略其他窗口）
        ns_window.orderFrontRegardless()
        
        # 设置窗口集合行为
        # 注意：CanJoinAllSpaces 和 MoveToActiveSpace 是互斥的
        # 我们需要先清除可能冲突的标志，然后设置我们需要的
        from Cocoa import NSWindowCollectionBehaviorMoveToActiveSpace
        
        behavior = 0  # 从 0 开始，避免继承冲突的标志
        
        # CanJoinAllSpaces: 窗口出现在所有空间（包括全屏应用的空间）
        behavior |= NSWindowCollectionBehaviorCanJoinAllSpaces
        
        # Stationary: 窗口不随空间切换而移动
        behavior |= NSWindowCollectionBehaviorStationary
        
        # FullScreenAuxiliary: 允许在全屏应用中显示
        behavior |= NSWindowCollectionBehaviorFullScreenAuxiliary
        
        ns_window.setCollectionBehavior_(behavior)
        
        if not silent:
            logger.info(f"macOS 全屏覆盖已启用 - 窗口: {widget.windowTitle() or widget.__class__.__name__}")
            logger.debug(f"窗口层级: {ns_window.level()} (NSStatusWindowLevel={NSStatusWindowLevel}, OVERLAY_LEVEL=1000)")
            logger.debug(f"集合行为: {hex(behavior)}")
        
    except ImportError as e:
        if not silent:
            logger.warning(f"macOS 覆盖功能不可用（缺少 pyobjc）: {e}")
    except Exception as e:
        if not silent:
            logger.error(f"macOS 全屏覆盖设置失败: {e}")


def disable_click_through(widget: QWidget):
    """
    禁用点击穿透（确保窗口可以接收鼠标事件）
    
    Args:
        widget: Qt 窗口对象
    """
    widget.setAttribute(Qt.WA_TransparentForMouseEvents, False)


def enable_click_through(widget: QWidget):
    """
    启用点击穿透（鼠标事件穿透到下层窗口）
    
    Args:
        widget: Qt 窗口对象
    
    注意：启用后窗口无法接收鼠标点击
    """
    widget.setAttribute(Qt.WA_TransparentForMouseEvents, True)


# 便捷别名
setup_overlay = enable_overlay_mode
