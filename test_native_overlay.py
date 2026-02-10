"""
纯 macOS 原生窗口测试 - 不使用 Qt

直接用 PyObjC 创建原生 NSWindow，测试是否能置顶
"""
import sys
from AppKit import (
    NSApplication, 
    NSWindow, 
    NSApp,
    NSBackingStoreBuffered,
    NSWindowStyleMaskTitled,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskMiniaturizable,
)
from Cocoa import (
    NSMakeRect,
    NSStatusWindowLevel,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowCollectionBehaviorStationary,
    NSWindowCollectionBehaviorFullScreenAuxiliary,
    NSTextField,
)
from PyObjCTools import AppHelper

def create_native_overlay_window():
    """创建原生 macOS 覆盖窗口"""
    # 创建应用
    app = NSApplication.sharedApplication()
    
    # 创建窗口
    rect = NSMakeRect(100, 100, 400, 300)
    style = (NSWindowStyleMaskTitled | 
             NSWindowStyleMaskClosable | 
             NSWindowStyleMaskMiniaturizable)
    
    window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        rect, style, NSBackingStoreBuffered, False
    )
    
    window.setTitle_("macOS 原生窗口置顶测试")
    
    # 设置窗口层级 - 使用最高级别
    OVERLAY_LEVEL = 1000
    window.setLevel_(OVERLAY_LEVEL)
    print(f"✅ 窗口层级设置为: {window.level()}")
    
    # 设置集合行为
    behavior = (NSWindowCollectionBehaviorCanJoinAllSpaces |
                NSWindowCollectionBehaviorStationary |
                NSWindowCollectionBehaviorFullScreenAuxiliary)
    window.setCollectionBehavior_(behavior)
    print(f"✅ 集合行为: {hex(behavior)}")
    
    # 强制前置
    window.orderFrontRegardless()
    window.makeKeyAndOrderFront_(None)
    print("✅ 窗口已强制前置")
    
    # 添加文本标签
    label = NSTextField.alloc().initWithFrame_(NSMakeRect(50, 100, 300, 100))
    label.setStringValue_(
        "🔍 纯 macOS 原生窗口测试\n\n"
        "如果这个窗口能在所有应用之上，\n"
        "说明 macOS API 本身是可以工作的。\n\n"
        "如果不行，可能是系统权限或限制问题。"
    )
    label.setEditable_(False)
    label.setBordered_(False)
    label.setBackgroundColor_(None)
    
    content_view = window.contentView()
    content_view.addSubview_(label)
    
    # 显示窗口
    window.makeKeyAndOrderFront_(None)
    
    print("=" * 60)
    print("原生窗口已创建")
    print("请检查此窗口是否在所有应用之上")
    print("按 Ctrl+C 退出")
    print("=" * 60)
    
    # 运行事件循环
    AppHelper.runEventLoop()

if __name__ == "__main__":
    create_native_overlay_window()
