"""
测试 macOS 窗口置顶功能

直接创建一个简单窗口，测试是否能置顶
"""
import sys
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton
from PySide6.QtCore import Qt
from utils.overlay_helper import enable_overlay_mode
from loguru import logger

# 配置日志
logger.remove()
logger.add(sys.stderr, level="DEBUG")

class TestOverlayWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("macOS 置顶测试窗口")
        self.resize(400, 300)
        
        layout = QVBoxLayout()
        
        # 提示文字
        label = QLabel(
            "🔍 macOS 窗口置顶测试\n\n"
            "如果这个窗口能在所有应用之上显示，\n"
            "包括全屏应用，说明置顶成功！\n\n"
            "尝试打开其他应用窗口，\n"
            "看看这个窗口是否始终在最前面。"
        )
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 14px; padding: 20px;")
        layout.addWidget(label)
        
        # 检查权限按钮
        check_btn = QPushButton("🔍 检查辅助功能权限")
        check_btn.clicked.connect(self.check_permission)
        layout.addWidget(check_btn)
        
        # 强制置顶按钮
        force_btn = QPushButton("⬆️ 强制置顶（重新应用设置）")
        force_btn.clicked.connect(self.force_on_top)
        layout.addWidget(force_btn)
        
        # 关闭按钮
        close_btn = QPushButton("❌ 关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
        
        # 启用覆盖模式
        logger.info("正在启用覆盖模式...")
        enable_overlay_mode(self, frameless=False, translucent=False)
        
    def check_permission(self):
        """检查辅助功能权限"""
        try:
            from ApplicationServices import AXIsProcessTrusted
            has_permission = AXIsProcessTrusted()
            
            if has_permission:
                logger.info("✅ 辅助功能权限：已授权")
                self.show_message("✅ 权限已授权", "辅助功能权限已正确配置")
            else:
                logger.warning("❌ 辅助功能权限：未授权")
                self.show_message(
                    "❌ 权限未授权",
                    "请前往：\n系统设置 > 隐私与安全性 > 辅助功能\n"
                    "添加 Visual Studio Code 或 Terminal"
                )
        except Exception as e:
            logger.error(f"检查权限失败: {e}")
    
    def force_on_top(self):
        """强制置顶"""
        logger.info("强制重新应用置顶设置...")
        try:
            # 重新启用覆盖模式
            enable_overlay_mode(self, frameless=False, translucent=False)
            
            # 额外：macOS 原生调用
            if sys.platform == "darwin":
                from AppKit import NSApp
                from Cocoa import NSStatusWindowLevel
                import objc
                from ctypes import c_void_p
                
                window_id = self.winId()
                ns_view = objc.objc_object(c_void_p=window_id)
                ns_window = ns_view.window()
                
                if ns_window:
                    current_level = ns_window.level()
                    ns_window.setLevel_(NSStatusWindowLevel)
                    logger.info(f"窗口层级：{current_level} → {ns_window.level()} (NSStatusWindowLevel={NSStatusWindowLevel})")
                    
                    # 强制刷新
                    ns_window.orderFrontRegardless()
                    logger.info("✅ 强制置顶完成")
                else:
                    logger.error("无法获取 NSWindow")
        except Exception as e:
            logger.error(f"强制置顶失败: {e}")
    
    def show_message(self, title, message):
        """显示消息"""
        from PySide6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec()
    
    def showEvent(self, event):
        """窗口显示时"""
        super().showEvent(event)
        logger.info("窗口已显示，检查窗口标志...")
        
        flags = self.windowFlags()
        logger.info(f"窗口标志: {flags}")
        logger.info(f"  - WindowStaysOnTopHint: {bool(flags & Qt.WindowStaysOnTopHint)}")
        logger.info(f"  - Tool: {bool(flags & Qt.Tool)}")
        logger.info(f"  - FramelessWindowHint: {bool(flags & Qt.FramelessWindowHint)}")
        
        # 自动检查权限
        self.check_permission()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = TestOverlayWindow()
    window.show()
    
    logger.info("=" * 60)
    logger.info("测试窗口已启动")
    logger.info("请尝试打开其他应用，看看此窗口是否始终在最前面")
    logger.info("=" * 60)
    
    sys.exit(app.exec())
