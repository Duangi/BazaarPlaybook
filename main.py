# main.py
import sys
import os
import json
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPropertyAnimation, QRect, QEasingCurve, QPoint
from gui.windows.start_window import StartWindow
from gui.windows.diagnostics_window import DiagnosticsWindow
from gui.windows.sidebar_window import SidebarWindow
from gui.windows.island_window import IslandWindow
from utils.logger import setup_logger
from gui.effects.holographic_collapse import HolographicCollapse

class BazaarApp:
    def __init__(self):
        # 初始化日志
        self.logger = setup_logger(is_gui_app=True)
        self.logger.info("主程序启动...")

        # 实例化窗口
        self.start_win = StartWindow()
        self.diag_win = DiagnosticsWindow()
        self.sidebar_win = SidebarWindow()
        self.island_win = IslandWindow()  # 灵动岛

        # 绑定信号
        self.start_win.entered.connect(self.on_start_enter)  # 启动助手
        self.start_win.diagnostic_requested.connect(self.show_diagnostics)  # 手动自检
        self.diag_win.enter_main_requested.connect(self.show_main_window)  # 诊断完成进入主界面
        self.diag_win.closed.connect(self.on_diagnostic_finished)  # 诊断完成
        
        # 侧边栏和灵动岛的联动
        self.sidebar_win.collapse_to_island.connect(self.collapse_sidebar_to_island)  # 收起到灵动岛
        self.island_win.expand_requested.connect(self.expand_island_to_sidebar)  # 展开侧边栏

    def run(self):
        """启动应用"""
        # 检查是否需要自动诊断
        if self._need_diagnostic():
            self.logger.info("检测到首次运行或配置缺失，自动启动诊断...")
            self.start_win.show()
            # 延迟一点显示诊断窗口，让开始窗口先显示
            from PySide6.QtCore import QTimer
            QTimer.singleShot(1000, self._auto_start_diagnostic)
        else:
            self.logger.info("配置完整，直接显示开始窗口...")
            self.start_win.show()

    def _need_diagnostic(self):
        """检查是否需要运行诊断"""
        settings_path = "user_data/settings.json"
        
        # 检查配置文件是否存在
        if not os.path.exists(settings_path):
            return True
            
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # 检查必需的配置项
            required_keys = [
                "yolo_fps",
                "best_ocr",
                "preferred_provider",
                "best_ocr_engine"
            ]
            
            for key in required_keys:
                if key not in settings:
                    self.logger.warning(f"配置缺失: {key}")
                    return True
                    
            self.logger.info("配置完整，跳过自动诊断")
            return False
            
        except Exception as e:
            self.logger.error(f"读取配置文件失败: {e}")
            return True
            
    def _auto_start_diagnostic(self):
        """自动启动诊断"""
        self.show_diagnostics()
        
    def on_start_enter(self):
        """点击启动助手按钮"""
        if self._need_diagnostic():
            # 配置不完整，提示需要先自检
            self.logger.warning("配置不完整，请先运行自检...")
            self.show_diagnostics()
        else:
            # 配置完整，显示主界面
            self.logger.info("进入主界面...")
            self.show_main_window()

    def show_diagnostics(self):
        """显示诊断窗口"""
        self.logger.info("正在开启自检流程...")
        self.diag_win.show()
        # 自动开始诊断
        self.diag_win.start_diagnosis()

    def on_diagnostic_finished(self):
        """诊断完成后的处理"""
        self.logger.info("诊断完成，准备进入主界面...")
        # 可以在这里添加延迟或直接显示主界面
        
    def show_main_window(self):
        """显示主界面（侧边栏）"""
        self.logger.info("显示主界面...")
        self.start_win.hide()
        self.diag_win.hide()
        self.island_win.hide()  # 隐藏灵动岛
        self.sidebar_win.show()
        
    def collapse_sidebar_to_island(self):
        """将侧边栏收起到灵动岛（全息收缩）"""
        self.logger.info("全息收缩：侧边栏 -> 灵动岛...")

        # 先确保灵动岛位置正确（但不显示），避免目标几何错误
        if hasattr(self.island_win, "_move_to_top_center"):
            self.island_win._move_to_top_center()
        self.island_win.hide()

        target_rect = QRect(self.island_win.geometry())

        def on_finished():
            self.sidebar_win.hide()
            self.island_win.show()
            # 还原侧边栏（下次展开从胶囊放大）
            self.sidebar_win.resize(self.sidebar_win.default_width, self.sidebar_win.default_height)
            self.sidebar_win._position_to_right()

        self._holo = HolographicCollapse(
            self.sidebar_win,
            target_rect,
            duration=560,
            enable_particles=True,
        )
        self._holo.start(on_finished)

    def expand_island_to_sidebar(self):
        """将灵动岛展开为侧边栏（几何展开）"""
        self.logger.info("展开：灵动岛 -> 侧边栏...")

        island_rect = QRect(self.island_win.geometry())
        self.sidebar_win.setGeometry(island_rect)
        self.sidebar_win.show()
        self.island_win.hide()

        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        end_rect = QRect(
            screen.width() - self.sidebar_win.default_width - 10,
            (screen.height() - self.sidebar_win.default_height) // 2,
            self.sidebar_win.default_width,
            self.sidebar_win.default_height,
        )

        anim = QPropertyAnimation(self.sidebar_win, b"geometry")
        anim.setDuration(520)
        anim.setStartValue(island_rect)
        anim.setEndValue(end_rect)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        self.expand_anim = anim

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置全局 UI 风格 (Fusion 风格在各平台最稳定)
    app.setStyle("Fusion")
    
    bazaar = BazaarApp()
    bazaar.run()
    
    sys.exit(app.exec())