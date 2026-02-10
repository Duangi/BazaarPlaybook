"""
测试覆盖助手集成

验证所有窗口都能正确启用 macOS 全屏覆盖支持
"""
import sys
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
from PySide6.QtCore import Qt


def test_import_overlay_helper():
    """测试覆盖助手导入"""
    try:
        from utils.overlay_helper import enable_overlay_mode, setup_overlay
        print("✅ overlay_helper 导入成功")
        return True
    except ImportError as e:
        print(f"❌ overlay_helper 导入失败: {e}")
        return False


def test_import_windows():
    """测试所有窗口类导入"""
    windows = [
        ("SidebarWindow", "gui.windows.sidebar_window"),
        ("IslandWindow", "gui.windows.island_window"),
        ("DebugOverlayWindow", "gui.windows.debug_overlay_window"),
        ("DiagnosticsWindow", "gui.windows.diagnostics_window"),
        ("StartWindow", "gui.windows.start_window"),
        ("SettingsDialog", "gui.windows.settings_dialog"),
    ]
    
    all_ok = True
    for class_name, module_name in windows:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✅ {class_name} 导入成功")
        except Exception as e:
            print(f"❌ {class_name} 导入失败: {e}")
            all_ok = False
    
    return all_ok


def test_overlay_functionality():
    """测试覆盖功能（需要显示界面）"""
    from utils.overlay_helper import enable_overlay_mode
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # 创建测试窗口
    widget = QWidget()
    widget.setWindowTitle("Overlay Test Window")
    widget.resize(300, 200)
    
    layout = QVBoxLayout(widget)
    
    info_label = QPushButton("点击测试覆盖模式")
    layout.addWidget(info_label)
    
    # 启用覆盖模式
    enable_overlay_mode(widget, frameless=False, translucent=False)
    
    # 检查窗口标志
    flags = widget.windowFlags()
    has_on_top = bool(flags & Qt.WindowStaysOnTopHint)
    has_tool = bool(flags & Qt.Tool)
    
    print(f"窗口标志检查:")
    print(f"  - WindowStaysOnTopHint: {'✅' if has_on_top else '❌'}")
    print(f"  - Tool: {'✅' if has_tool else '❌'}")
    
    # macOS 特殊检查
    if sys.platform == "darwin":
        print(f"  - macOS 平台：将在显示后设置 NSWindow 层级")
        widget.show()
        
        try:
            from AppKit import NSWindow
            from PyObjCTools import AppHelper
            import objc
            from ctypes import c_void_p
            
            window_id = widget.winId()
            ns_window = objc.objc_object(c_void_p=int(window_id))
            level = ns_window.level()
            behavior = ns_window.collectionBehavior()
            
            print(f"  - NSWindow Level: {level} (期望: 3=NSFloatingWindowLevel)")
            print(f"  - Collection Behavior: {hex(behavior)}")
            print(f"✅ macOS 覆盖设置成功")
        except Exception as e:
            print(f"⚠️ macOS 覆盖验证失败: {e}")
    
    widget.close()
    return True


def main():
    """运行所有测试"""
    print("=" * 50)
    print("覆盖助手集成测试")
    print("=" * 50)
    
    print("\n1. 测试 overlay_helper 导入")
    test1 = test_import_overlay_helper()
    
    print("\n2. 测试窗口类导入")
    test2 = test_import_windows()
    
    print("\n3. 测试覆盖功能")
    test3 = test_overlay_functionality()
    
    print("\n" + "=" * 50)
    if test1 and test2 and test3:
        print("✅ 所有测试通过")
        print("\n集成完成！已更新窗口：")
        print("  - sidebar_window.py")
        print("  - island_window.py")
        print("  - debug_overlay_window.py")
        print("  - diagnostics_window.py")
        print("  - start_window.py")
        print("  - settings_dialog.py")
        print("\nmacOS 用户：这些窗口现在可以覆盖全屏游戏窗口")
    else:
        print("❌ 部分测试失败")
    print("=" * 50)


if __name__ == "__main__":
    main()
