# main.py
import sys
import os
import ctypes
import json
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPropertyAnimation, QRect, QEasingCurve, QPoint
from gui.windows.start_window import StartWindow
from gui.windows.diagnostics_window import DiagnosticsWindow
from gui.windows.sidebar_window import SidebarWindow
from gui.windows.island_window import IslandWindow
from gui.windows.debug_overlay_window import DebugOverlayWindow
from utils.logger import setup_logger
from gui.effects.holographic_collapse import HolographicCollapse
from services.auto_scanner import AutoScanner
from data_manager.config_manager import ConfigManager
from gui.widgets.scanner_detail_window import ScannerDetailWindow

class BazaarApp:
    def __init__(self):
        # 配置管理器
        self.config_manager = ConfigManager()
        
        # 初始化日志 (根据配置决定是否开启调试模式)
        debug_mode = self.config_manager.settings.get("debug_mode", False)
        self.logger = setup_logger(is_gui_app=True, debug_mode=debug_mode)
        self.logger.info(f"主程序启动... (Debug Mode: {debug_mode})")

        # 实例化窗口
        self.start_win = StartWindow()
        self.diag_win = DiagnosticsWindow()
        self.sidebar_win = SidebarWindow()
        self.island_win = IslandWindow()  # 灵动岛
        self.debug_win = DebugOverlayWindow() # 调试窗口
        self.scanner_result_win = ScannerDetailWindow() # 扫描结果独立窗口

        # 自动扫描服务
        self.auto_scanner = AutoScanner(self.config_manager)

        # 连接自动扫描信号
        self.auto_scanner.show_detail.connect(self.on_scanner_show_detail)      
        self.auto_scanner.hide_detail.connect(self.on_scanner_hide_detail)
        self.auto_scanner.force_show_detail.connect(self.on_scanner_force_show_detail)
        # 预识别反馈 (灵动岛)
        self.auto_scanner.item_pre_detected.connect(self.on_item_pre_detected)
        # 状态更新到 Island
        self.auto_scanner.status_changed.connect(self.on_scanner_status_changed)
        # 调试数据更新
        self.auto_scanner.scan_results_updated.connect(self.debug_win.update_data)
        if hasattr(self.sidebar_win, 'settings_page'):
            self.sidebar_win.settings_page.reset_overlay_pos_requested.connect(
                self.sidebar_win.monster_page.reset_detail_window_position
            )
            # 共享 ConfigManager
            self.sidebar_win.settings_page.config_manager = self.config_manager

        # 绑定信号
        self.start_win.entered.connect(self.on_start_enter)  # 启动助手
        self.start_win.diagnostic_requested.connect(self.show_diagnostics)  # 手动自检
        self.diag_win.enter_main_requested.connect(self.show_main_window)  # 诊断完成进入主界面
        self.diag_win.closed.connect(self.on_diagnostic_finished)  # 诊断完成
        
        # 侧边栏和灵动岛的联动
        self.sidebar_win.collapse_to_island.connect(self.collapse_sidebar_to_island)  # 收起到灵动岛
        # self.island_win.expand_requested.connect(self.expand_island_to_sidebar)  # 展开侧边栏 (原逻辑)
        self.island_win.expand_requested.connect(self.show_debug_window) # 双击灵动岛显示调试窗口
        
    def show_debug_window(self):
        """显示/隐藏调试窗口"""
        if self.debug_win.isVisible():
            self.debug_win.hide()
        else:
            self.debug_win.show()

    def _need_diagnostic(self):
        """检查是否需要运行诊断"""
        # ... logic ...
        return False # Placeholder if needed, but keeping original logic implies I shouldn't replace this unless I read it. 
        # I will just insert the wrapper methods at the end of class or before run


    def on_scanner_show_detail(self, dtype, obj_id):
        """Scanner detected something (with optional delay)"""
        # Read delay setting
        delay = self.config_manager.settings.get("hover_delay", 200)
        
        # If pending show exists, check if same object.
        if hasattr(self, '_pending_show') and self._pending_show:
            if self._pending_show['id'] == obj_id:
                return # Already pending
            else:
                self._cancel_pending_show()

        # Stop any existing popup if switching target?
        # Actually standard logic: new show replaces old.
        # But for delay, we wait.
        
        if delay > 0:
            if not hasattr(self, '_show_timer'):
                from PySide6.QtCore import QTimer
                self._show_timer = QTimer(self.context_dummy_widget if hasattr(self, 'context_dummy_widget') else self.sidebar_win)
                self._show_timer.setSingleShot(True)
                self._show_timer.timeout.connect(self._execute_show_detail)
            
            self._pending_show = {'dtype': dtype, 'id': obj_id}
            self._show_timer.start(int(delay))
        else:
            self._perform_show(dtype, obj_id)

    def _cancel_pending_show(self):
        if hasattr(self, '_show_timer') and self._show_timer.isActive():
            self._show_timer.stop()
        self._pending_show = None

    def _execute_show_detail(self):
        if hasattr(self, '_pending_show') and self._pending_show:
            self._perform_show(self._pending_show['dtype'], self._pending_show['id'])
            self._pending_show = None

    def _perform_show(self, dtype, obj_id):
        if dtype == "monster":
             self.sidebar_win.monster_page.show_floating_detail_by_id(obj_id)
        elif dtype == "card":
             self.scanner_result_win.show_item(obj_id)

    def on_scanner_force_show_detail(self, dtype, obj_id):
        """Hotkey pressed - Show immediately and sticky"""
        self._cancel_pending_show() # Cancel any delayed regular hover
        
        if dtype == "monster":
             # Monster window doesn't support generic sticky mode yet via this path, 
             # but we can just show it. 
             self.sidebar_win.monster_page.show_floating_detail_by_id(obj_id)
        elif dtype == "card":
             self.scanner_result_win.show_item(obj_id, sticky=True)

    def on_item_pre_detected(self, dtype, obj_id, name):
        """
        Scan detected item under mouse (hover > 200ms).
        Show feedback on Island Window.
        """
        # 1. Show feedback on Island Window
        self.island_win.show_detection_feedback(name)
        
        # 2. Maybe preload in scanner window without showing?
        # self.scanner_result_win.preload(obj_id) # Optimization if needed


    def on_scanner_hide_detail(self):
        """Scanner lost target"""
        self._cancel_pending_show()
        
        # Only hide if NOT sticky
        if not getattr(self.scanner_result_win, 'is_sticky', False):
            self.sidebar_win.monster_page.hide_detail()
            if self.scanner_result_win.isVisible():
                self.scanner_result_win.hide()

    def on_scanner_status_changed(self, active, msg):
        self.island_win.set_scanner_status(active, msg)

    def run(self):
        """启动应用"""
        # Start Scanner
        self.auto_scanner.start()
        
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
        
        # 默认不显示灵动岛，因为已经展开为侧边栏了
        # 但如果 AutoScan 开启，我们应该显示灵动岛用于状态展示？
        # 目前设计是 Sidebar 和 Island 互斥（收起/展开关系）。
        # 如果需要在 Sidebar 打开时也显示状态，应该在 Sidebar 上显示。
        # 既然用户要求 "tell me on the island"（即使 Sidebar 打开），
        # 我们可以暂时允许两者共存，或者修改逻辑。
        # 但为了满足 "在灵动岛上告诉我"，我强制显示灵动岛。
        self.island_win.show()
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
    # 强制开启 DPI 感知 (解决 4K 屏幕截图分辨率不匹配问题)
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = QApplication(sys.argv)
    
    # 设置全局 UI 风格 (Fusion 风格在各平台最稳定)
    app.setStyle("Fusion")
    
    bazaar = BazaarApp()
    bazaar.run()
    
    sys.exit(app.exec())