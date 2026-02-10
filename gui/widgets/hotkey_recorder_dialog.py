"""
Hotkey Recorder Dialog
弹窗捕获键盘与鼠标按键
"""
import sys
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFrame
from PySide6.QtCore import Qt, Signal, QThread, Slot
from PySide6.QtGui import QFont

from gui.styles import COLOR_GOLD

# keyboard 和 mouse 库在 macOS 上可能导致段错误，仅在 Windows 上使用
if sys.platform == "win32":
    try:
        import keyboard
        import mouse
    except ImportError:
        keyboard = None
        mouse = None
else:
    keyboard = None
    mouse = None

class RecorderWorker(QThread):
    """后台监听线程"""
    finished = Signal(str) # return the key string

    def __init__(self):
        super().__init__()
        self.listening = False
        self._keyboard_hook = None
        self._mouse_hook = None

    def run(self):
        self.listening = True
        
        # 在非 Windows 平台上，keyboard/mouse 不可用
        if keyboard is None or mouse is None:
            self.finished.emit("UNSUPPORTED_PLATFORM")
            return
        
        # We need a way to block/wait or just setup hooks and wait for signal
        # Since hooks are callbacks, we can just use a loop or wait condition.
        # But QThread run method is blocking.
        # Keyboard library hooks are global and run in their own threads usually.
        
        # Strategy: Setup hooks, then sleep loop until captured.
        
        self.capture = None
        
        def k_callback(e):
            if not self.listening: return
            if e.event_type == keyboard.KEY_DOWN:
                # Ignore isolated modifiers? No, user might want "Ctrl" as a key?
                # Usually we accept any key down.
                # Special handling for ESC ?
                if e.name == 'esc':
                    self.capture = 'ESCAPE_CANCEL'
                else:
                    self.capture = e.name # e.g. 'f1', 'a'
                self.listening = False

        def m_callback(e):
            if not self.listening: return
            if isinstance(e, mouse.ButtonEvent) and e.event_type == mouse.UP: 
                # Use UP event for mouse to avoid capturing the click that opened the dialog?
                # Or DOWN? If we use DOWN, we might catch the 'release' of the button that clicked the "Set" button.
                # Wait, "Set" button click: DOWN -> UP. Then Dialog opens.
                # So we are safe to listen for DOWN of NEXT event.
                # BUT, if user clicks "Left" on the dialog to cancel?
                pass
            
            if isinstance(e, mouse.ButtonEvent) and e.event_type == mouse.DOWN:
                # Filter left click if it might be interacting with UI?
                # User wants "Any key".
                # Let's map it.
                btn = e.button
                self.capture = f"mouse:{btn}"
                self.listening = False

        try:
            self._keyboard_hook = keyboard.hook(k_callback)
            self._mouse_hook = mouse.hook(m_callback)
            
            while self.listening:
                self.msleep(50)
                
        except Exception as e:
            print(f"Recorder Error: {e}")
        finally:
            # Cleanup
            try:
                if self._keyboard_hook: keyboard.unhook(self._keyboard_hook)
                if self._mouse_hook: mouse.unhook(self._mouse_hook)
            except:
                pass
        
        if self.capture:
            self.finished.emit(self.capture)

    def stop(self):
        self.listening = False


class HotkeyRecorderDialog(QDialog):
    hotkey_recorded = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置热键")
        # 取消固定大小，改为全屏覆盖以显示遮罩
        # self.setFixedSize(400, 200)
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Style - 黑色半透明背景遮罩
        self.setStyleSheet(f"""
            QDialog {{
                background-color: rgba(0, 0, 0, 0.7);
            }}
            #ContentFrame {{
                background-color: rgba(30, 30, 35, 0.95);
                border: 2px solid {COLOR_GOLD};
                border-radius: 12px;
            }}
            QLabel {{ color: #eee; }}
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.1);
                color: #fff;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 6px 15px;
            }}
            QPushButton:hover {{ background-color: rgba(255, 255, 255, 0.2); }}
        """)

        # 主布局 - 用于居中内容
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setAlignment(Qt.AlignCenter)

        # 内容容器
        self.content_frame = QFrame()
        self.content_frame.setObjectName("ContentFrame")
        self.content_frame.setFixedSize(400, 200)
        
        # 内容布局
        layout = QVBoxLayout(self.content_frame)
        layout.setSpacing(20)
        layout.setContentsMargins(30,30,30,30)

        # Icon/Title
        title = QLabel("⌨️ 请按下按键")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        layout.addWidget(title)

        # Desc
        desc = QLabel("支持键盘按键与鼠标按键 (左键/右键/侧键)\n按 ESC 取消")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #aaa; font-size: 11pt;")
        layout.addWidget(desc)
        
        # Buttons
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # 将内容容器添加到主布局
        main_layout.addWidget(self.content_frame)

        self.worker = None

    def showEvent(self, event):
        # 自动全屏覆盖
        if self.parent():
            # 如果有父窗口，覆盖父窗口区域
            parent_geo = self.parent().geometry()
            self.setGeometry(parent_geo)
        else:
            # 否则全屏
            from PySide6.QtGui import QGuiApplication
            screen = QGuiApplication.primaryScreen().geometry()
            self.setGeometry(screen)
            
        super().showEvent(event)
        # Start recording after short delay to avoid catching the triggering click
        from PySide6.QtCore import QTimer
        QTimer.singleShot(300, self.start_worker)

    def start_worker(self):
        self.worker = RecorderWorker()
        self.worker.finished.connect(self.on_recorded)
        self.worker.start()

    def on_recorded(self, key_str):
        if key_str == 'ESCAPE_CANCEL' or key_str == 'esc':
            self.reject()
        else:
            self.hotkey_recorded.emit(key_str)
            self.accept()
    
    def closeEvent(self, event):
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        super().closeEvent(event)
    
    def reject(self):
        if self.worker:
            self.worker.stop()
        super().reject()

