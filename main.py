# main.py
import sys
from PySide6.QtWidgets import QApplication
from gui.windows.start_window import StartWindow
from gui.windows.diagnostics_window import DiagnosticsWindow
from utils.logger import setup_logger

class BazaarApp:
    def __init__(self):
        # 初始化日志
        self.logger = setup_logger(is_gui_app=True)
        self.logger.info("主程序启动...")

        # 实例化窗口
        self.start_win = StartWindow()
        self.diag_win = DiagnosticsWindow()

        # 绑定进入信号：点击开始页按钮 -> 弹出自检页
        self.start_win.entered.connect(self.show_diagnostics)

    def run(self):
        self.start_win.show()

    def show_diagnostics(self):
        self.logger.info("正在开启自检流程...")
        self.diag_win.show()
        # 自动开始诊断
        self.diag_win.start_diagnosis()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置全局 UI 风格 (Fusion 风格在各平台最稳定)
    app.setStyle("Fusion")
    
    bazaar = BazaarApp()
    bazaar.run()
    
    sys.exit(app.exec())