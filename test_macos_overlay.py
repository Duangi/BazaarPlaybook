"""
macOS 全屏覆盖集成示例

演示如何在现有的 Qt 窗口中启用 macOS 全屏游戏覆盖功能
"""
import sys
from PySide6.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from PySide6.QtCore import Qt

# 导入 macOS 覆盖支持
from platforms.macos.overlay import setup_window_overlay


class OverlayWindow(QWidget):
    """演示覆盖窗口"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_overlay()
    
    def setup_ui(self):
        """设置 UI"""
        self.setWindowTitle("Overlay Demo")
        self.resize(400, 300)
        
        layout = QVBoxLayout()
        label = QLabel("这个窗口应该能覆盖全屏游戏")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 180);
                color: white;
                font-size: 20px;
                padding: 20px;
                border-radius: 10px;
            }
        """)
        layout.addWidget(label)
        self.setLayout(layout)
    
    def setup_overlay(self):
        """设置覆盖功能"""
        # 使用跨平台覆盖设置
        setup_window_overlay(self)
        
        print(f"平台: {sys.platform}")
        print(f"窗口标志: {self.windowFlags()}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    window = OverlayWindow()
    window.show()
    
    print("\n测试说明：")
    print("1. 运行一个全屏应用（如游戏）")
    print("2. 检查这个窗口是否仍然可见")
    print("3. macOS: 应该能覆盖全屏应用")
    print("4. Windows/Linux: 应该保持在最上层")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
