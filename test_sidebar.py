# test_sidebar.py
"""测试侧边栏界面"""
import sys
from PySide6.QtWidgets import QApplication
from gui.windows.sidebar_window import SidebarWindow
from utils.logger import setup_logger

if __name__ == "__main__":
    # 初始化日志
    logger = setup_logger(is_gui_app=True)
    logger.info("启动侧边栏测试...")
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 创建侧边栏
    sidebar = SidebarWindow()
    sidebar.show()
    
    sys.exit(app.exec())
