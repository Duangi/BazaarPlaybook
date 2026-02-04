from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QHBoxLayout
from PySide6.QtCore import Qt, QThread, Signal
from loguru import logger
import onnxruntime as ort
import os
import config
from platforms.adapter import PlatformAdapter

class DiagnosticThread(QThread):
    """异步检测线程，防止检查过程卡死UI"""
    finished = Signal(dict)

    def run(self):
        results = {}
        # 1. 检查模型文件
        results['model'] = os.path.exists(config.MODEL_PATH)
        
        # 2. 检查GPU加速
        providers = ort.get_available_providers()
        results['gpu'] = "DmlExecutionProvider" in providers or "CUDAExecutionProvider" in providers
        results['gpu_name'] = providers[0] if providers else "None"

        # 3. 检查OCR
        try:
            engine = PlatformAdapter.get_ocr_engine()
            results['ocr'] = engine.name if engine else "Unavailable"
        except:
            results['ocr'] = "Error"

        # 4. 检查数据库
        results['db'] = os.path.exists(config.ITEMS_DB_PATH)

        self.finished.emit(results)

class DiagnosticsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("系统自检")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(400, 500)

        # UI 布局 (黑金风格)
        self.main_layout = QVBoxLayout(self)
        self.container = QFrame()
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: {config.COLOR_MAIN_BG};
                border: 2px solid {config.COLOR_GOLD};
                border-radius: 12px;
            }}
            QLabel {{ border: none; color: white; font-size: 14px; }}
            .Success {{ color: #4CAF50; font-weight: bold; }}
            .Fail {{ color: #F44336; font-weight: bold; }}
        """)
        self.main_layout.addWidget(self.container)
        
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(30, 30, 30, 30)

        self.title = QLabel("核心组件自检")
        self.title.setStyleSheet(f"color: {config.COLOR_GOLD}; font-size: 20px; font-weight: bold;")
        self.layout.addWidget(self.title, alignment=Qt.AlignCenter)
        self.layout.addSpacing(20)

        # 状态条目列表
        self.items = {}
        for key, label in [("model", "YOLO 模型文件"), ("gpu", "硬件加速 (GPU)"), 
                           ("ocr", "OCR 识别引擎"), ("db", "卡牌数据库")]:
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            status = QLabel("检测中...")
            row.addWidget(status, alignment=Qt.AlignRight)
            self.items[key] = status
            self.layout.addLayout(row)

        self.layout.addStretch()
        
        self.close_btn = QPushButton("返回主界面")
        self.close_btn.setStyleSheet(f"background: {config.COLOR_GOLD}; color: black; padding: 8px;")
        self.close_btn.clicked.connect(self.hide)
        self.layout.addWidget(self.close_btn)

    def start_check(self):
        self.thread = DiagnosticThread()
        self.thread.finished.connect(self.update_ui)
        self.thread.start()

    def update_ui(self, results):
        # 更新显示逻辑
        self.set_status("model", "已就绪" if results['model'] else "缺失", results['model'])
        self.set_status("gpu", f"开启 ({results['gpu_name']})" if results['gpu'] else "未开启 (使用CPU)", results['gpu'])
        self.set_status("ocr", results['ocr'], results['ocr'] != "Error")
        self.set_status("db", "正常" if results['db'] else "缺失", results['db'])

    def set_status(self, key, text, success):
        label = self.items[key]
        label.setText(text)
        label.setProperty("class", "Success" if success else "Fail")
        label.style().unpolish(label)
        label.style().polish(label)