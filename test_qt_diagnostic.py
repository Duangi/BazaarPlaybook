"""
Qt 窗口层级诊断工具

实时监控 Qt 窗口的层级变化，诊断为什么窗口不能置顶
"""
import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit
from PySide6.QtCore import Qt, QTimer
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="DEBUG")

class DiagnosticWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qt 窗口层级诊断")
        self.resize(500, 600)
        
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("🔍 Qt + macOS 窗口层级诊断工具")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # 日志输出
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        # 按钮
        check_btn = QPushButton("📊 检查当前状态")
        check_btn.clicked.connect(self.check_status)
        layout.addWidget(check_btn)
        
        apply_btn = QPushButton("⬆️ 应用置顶设置")
        apply_btn.clicked.connect(self.apply_overlay)
        layout.addWidget(apply_btn)
        
        monitor_btn = QPushButton("🔄 开始/停止监控 (每秒)")
        monitor_btn.clicked.connect(self.toggle_monitor)
        layout.addWidget(monitor_btn)
        
        close_btn = QPushButton("❌ 关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
        
        # 定时器
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.check_status)
        self.monitoring = False
        
        # 初始设置
        self.apply_overlay()
        
    def log(self, msg):
        """添加日志"""
        self.log_text.append(msg)
        logger.info(msg)
        
    def check_status(self):
        """检查窗口状态"""
        self.log("\n" + "=" * 50)
        self.log("🔍 检查窗口状态...")
        
        # Qt 标志
        flags = self.windowFlags()
        self.log(f"Qt 窗口标志: {flags}")
        self.log(f"  - WindowStaysOnTopHint: {bool(flags & Qt.WindowStaysOnTopHint)}")
        self.log(f"  - Tool: {bool(flags & Qt.Tool)}")
        self.log(f"  - FramelessWindowHint: {bool(flags & Qt.FramelessWindowHint)}")
        
        # macOS 原生检查
        if sys.platform == "darwin":
            try:
                from AppKit import NSApp
                from Cocoa import NSStatusWindowLevel
                import objc
                from ctypes import c_void_p
                
                window_id = self.winId()
                ns_view = objc.objc_object(c_void_p=window_id)
                ns_window = ns_view.window()
                
                if ns_window:
                    level = ns_window.level()
                    behavior = ns_window.collectionBehavior()
                    
                    self.log(f"\nmacOS NSWindow 状态:")
                    self.log(f"  - 窗口层级: {level}")
                    self.log(f"    (NSNormalWindowLevel=0, NSFloatingWindowLevel=3,")
                    self.log(f"     NSStatusWindowLevel=25, 目标=1000)")
                    self.log(f"  - 集合行为: {hex(behavior)}")
                    self.log(f"  - 是否可见: {ns_window.isVisible()}")
                    self.log(f"  - 是否关键窗口: {ns_window.isKeyWindow()}")
                    self.log(f"  - 是否主窗口: {ns_window.isMainWindow()}")
                    
                    # 诊断问题
                    if level < 1000:
                        self.log(f"\n⚠️  问题: 窗口层级过低 ({level})，应该是 1000")
                    else:
                        self.log(f"\n✅ 窗口层级正确: {level}")
                        
                else:
                    self.log("\n❌ 错误: 无法获取 NSWindow 对象")
                    
            except Exception as e:
                self.log(f"\n❌ macOS 检查失败: {e}")
                import traceback
                self.log(traceback.format_exc())
        
        self.log("=" * 50)
        
    def apply_overlay(self):
        """应用置顶设置"""
        self.log("\n🔧 应用置顶设置...")
        
        # 1. Qt 标志
        flags = Qt.WindowStaysOnTopHint | Qt.Tool
        self.setWindowFlags(flags)
        self.show()  # 重新显示
        self.log(f"✅ Qt 标志已设置: {flags}")
        
        # 2. macOS 原生
        if sys.platform == "darwin":
            QTimer.singleShot(100, self._apply_macos_overlay)
    
    def _apply_macos_overlay(self):
        """应用 macOS 原生覆盖"""
        try:
            from AppKit import NSApp
            from Cocoa import (
                NSStatusWindowLevel,
                NSWindowCollectionBehaviorCanJoinAllSpaces,
                NSWindowCollectionBehaviorStationary,
                NSWindowCollectionBehaviorFullScreenAuxiliary,
            )
            import objc
            from ctypes import c_void_p
            
            window_id = self.winId()
            ns_view = objc.objc_object(c_void_p=window_id)
            ns_window = ns_view.window()
            
            if ns_window:
                # 设置层级
                OVERLAY_LEVEL = 1000
                ns_window.setLevel_(OVERLAY_LEVEL)
                
                # 设置行为
                behavior = (NSWindowCollectionBehaviorCanJoinAllSpaces |
                           NSWindowCollectionBehaviorStationary |
                           NSWindowCollectionBehaviorFullScreenAuxiliary)
                ns_window.setCollectionBehavior_(behavior)
                
                # 强制前置
                ns_window.orderFrontRegardless()
                ns_window.makeKeyAndOrderFront_(None)
                
                self.log(f"✅ macOS 原生设置完成")
                self.log(f"   层级: {ns_window.level()}")
                self.log(f"   行为: {hex(behavior)}")
            else:
                self.log("❌ 无法获取 NSWindow")
                
        except Exception as e:
            self.log(f"❌ macOS 设置失败: {e}")
            import traceback
            self.log(traceback.format_exc())
    
    def toggle_monitor(self):
        """开始/停止监控"""
        if self.monitoring:
            self.monitor_timer.stop()
            self.monitoring = False
            self.log("\n🛑 监控已停止")
        else:
            self.monitor_timer.start(1000)  # 每秒检查
            self.monitoring = True
            self.log("\n▶️  开始监控 (每秒检查一次)")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = DiagnosticWindow()
    window.show()
    
    print("=" * 60)
    print("诊断窗口已启动")
    print("1. 点击'检查当前状态'查看窗口信息")
    print("2. 点击'应用置顶设置'重新设置")
    print("3. 点击'开始监控'实时监控窗口状态变化")
    print("=" * 60)
    
    sys.exit(app.exec())
