import cv2
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QFrame, QTextEdit, QScrollArea, QGridLayout)
from PySide6.QtCore import Qt, QThread, Signal, QPoint
from PySide6.QtGui import QTextCursor
from loguru import logger

import config
from gui.styles import DIAGNOSTICS_STYLE
from utils.overlay_helper import enable_overlay_mode
from gui.components.styled_button import StyledButton
from gui.components.info_card import InfoCard
from core.diagnostics import SystemDiagnostics
from data_manager.config_manager import ConfigManager

class DiagWorker(QThread):
    log_signal = Signal(str)
    task_done_signal = Signal(str)
    result_signal = Signal(dict)

    def run(self):
        # ✅ 这里是核心：拦截全程序的 logger 并转换为 HTML
        def ui_sink(message):
            rec = message.record
            color_map = {
                "DEBUG": "#666666", "INFO": "#58a6ff", "SUCCESS": "#3fb950",
                "WARNING": "#d29922", "ERROR": "#f85149"
            }
            level = rec["level"].name
            color = color_map.get(level, "#eee")
            html = f"<span style='color:{color}; font-family:Consolas;'>[{level: <7}]</span> {rec['message']}"
            self.log_signal.emit(html)

        sink_id = logger.add(ui_sink, level="DEBUG", format="{message}")
        
        try:
            diag = SystemDiagnostics()
            report = {}
            
            logger.info("开始自检流程...")
            report['env'] = diag.check_environment()
            self.task_done_signal.emit("env")
            
            test_img_path = "tests/assets/detail/detail_1.png"
            report['yolo'] = diag.benchmark_yolo(test_img_path)
            self.task_done_signal.emit("yolo")
            
            # ORB 匹配测试 - 使用与 bench_matcher 相同的测试图片
            logger.info("开始 ORB 特征匹配测试...")
            test_samples = {
                'Small': cv2.imread('tests/assets/small.png'),
                'Medium': cv2.imread('tests/assets/medium.png'),
                'Large': cv2.imread('tests/assets/large.png')
            }
            report['orb'] = diag.benchmark_matcher(test_samples)
            self.task_done_signal.emit("orb")
            
            test_img = cv2.imread(test_img_path)
            report['ocr'] = diag.benchmark_ocr(test_img)
            self.task_done_signal.emit("ocr")

            self.result_signal.emit(report)
        except Exception as e:
            logger.error(f"异常中断: {e}")
        finally:
            logger.remove(sink_id)

class DiagnosticsWindow(QWidget):
    """诊断窗口"""
    
    enter_main_requested = Signal()  # 新增：请求进入主界面的信号
    closed = Signal()  # 窗口关闭信号
    
    def __init__(self):
        super().__init__()
        # 使用跨平台覆盖助手（自动处理 macOS 全屏支持）
        enable_overlay_mode(self, frameless=True, translucent=True)
        self.resize(1000, 650)
        self._drag_pos = QPoint()  # 初始化拖动位置
        self._setup_ui()
        self.setStyleSheet(DIAGNOSTICS_STYLE)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.main_frame = QFrame()
        self.main_frame.setObjectName("MainFrame")
        layout.addWidget(self.main_frame)
        
        main_layout = QVBoxLayout(self.main_frame)
        main_layout.setContentsMargins(45, 40, 45, 40)
        main_layout.setSpacing(20)
        
        # 顶部标题区
        header_layout = QHBoxLayout()
        header = QLabel("🔍 系统环境诊断")
        header.setObjectName("DiagHeader")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        # 关闭按钮
        self.btn_close = StyledButton("✕", button_type="close")
        self.btn_close.setFixedSize(32, 32)
        self.btn_close.clicked.connect(self._on_close)
        header_layout.addWidget(self.btn_close)
        main_layout.addLayout(header_layout)

        # 主体区域
        body = QHBoxLayout()
        body.setSpacing(25)
        
        # 左侧任务面板
        task_container = QFrame()
        task_container.setObjectName("TaskPanel")
        task_layout = QVBoxLayout(task_container)
        task_layout.setContentsMargins(20, 20, 20, 20)
        task_layout.setSpacing(15)
        
        task_title = QLabel("检测项目")
        task_title.setObjectName("TaskTitle")
        task_layout.addWidget(task_title)
        
        self.tasks = {
            "env": self._create_task_item("基础文件检查", "检查核心文件和依赖"),
            "yolo": self._create_task_item("视觉识别压测", "YOLO模型性能测试"),
            "orb": self._create_task_item("图片匹配测试", "ORB特征匹配性能评估"),
            "ocr": self._create_task_item("文字识别测试", "OCR引擎性能评估")
        }
        
        for task_widget in self.tasks.values():
            task_layout.addWidget(task_widget)
        
        task_layout.addStretch()
        body.addWidget(task_container, 3)

        # 右侧控制台
        console_container = QFrame()
        console_container.setObjectName("ConsolePanel")
        console_layout = QVBoxLayout(console_container)
        console_layout.setContentsMargins(0, 0, 0, 0)
        console_layout.setSpacing(10)
        
        console_header = QLabel("📋 运行日志")
        console_header.setObjectName("ConsoleHeader")
        console_header.setContentsMargins(15, 10, 0, 0)
        console_layout.addWidget(console_header)
        
        self.console = QTextEdit()
        self.console.setObjectName("LogConsole")
        self.console.setReadOnly(True)
        console_layout.addWidget(self.console)
        
        body.addWidget(console_container, 7)
        main_layout.addLayout(body)

        # 结果卡片（初始隐藏）
        self.result_card = InfoCard()
        self.result_card.hide()
        main_layout.addWidget(self.result_card)

        # 底部按钮
        footer = QHBoxLayout()
        footer.addStretch()
        
        self.btn_run = StyledButton("开始检测", button_type="primary")
        self.btn_run.setFixedSize(150, 45)
        self.btn_run.clicked.connect(self.start_diagnosis)
        
        self.btn_enter = StyledButton("进入主界面", button_type="primary")
        self.btn_enter.setFixedSize(150, 45)
        self.btn_enter.setEnabled(False)
        self.btn_enter.clicked.connect(self._on_enter_main)

        footer.addWidget(self.btn_run)
        footer.addWidget(self.btn_enter)
        main_layout.addLayout(footer)

    def _create_task_item(self, title: str, desc: str):
        """创建任务项组件"""
        container = QFrame()
        container.setObjectName("TaskItem")
        container.setProperty("status", "idle")
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(12, 10, 12, 10)
        
        # 状态指示器
        status_indicator = QLabel("○")
        status_indicator.setObjectName("StatusIndicator")
        status_indicator.setFixedWidth(20)
        layout.addWidget(status_indicator)
        
        # 文字区域
        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)
        
        title_label = QLabel(title)
        title_label.setObjectName("TaskTitle")
        text_layout.addWidget(title_label)
        
        desc_label = QLabel(desc)
        desc_label.setObjectName("TaskDesc")
        text_layout.addWidget(desc_label)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        # 保存引用以便后续更新
        container.status_indicator = status_indicator
        container.title_label = title_label
        
        return container

    def start_diagnosis(self):
        self.btn_run.setEnabled(False)
        self.console.clear()
        self.result_card.hide()
        
        # 重置所有任务状态
        for task_widget in self.tasks.values():
            task_widget.setProperty("status", "idle")
            task_widget.status_indicator.setText("○")
            task_widget.style().unpolish(task_widget)
            task_widget.style().polish(task_widget)

        self.worker = DiagWorker()
        self.worker.log_signal.connect(self.append_log)
        self.worker.task_done_signal.connect(self.mark_done)
        self.worker.result_signal.connect(self.finish)
        self.worker.start()

    def append_log(self, html):
        self.console.append(html)
        self.console.moveCursor(QTextCursor.MoveOperation.End)

    def mark_done(self, key):
        task_widget = self.tasks[key]
        task_widget.setProperty("status", "done")
        task_widget.status_indicator.setText("●")
        task_widget.style().unpolish(task_widget)
        task_widget.style().polish(task_widget)

    def finish(self, report):
        self.btn_run.setEnabled(True)
        self.btn_enter.setEnabled(True)
        
        # 保存配置
        yolo_provider = report['yolo']['best_provider']
        yolo_avg_ms = report['yolo'].get('avg_ms', 0)
        yolo_fps = report['yolo'].get('suggested_fps', 30)
        
        ocr_engine = report['ocr']['best_engine_name']
        ocr_avg_ms = report['ocr']['all'][0]['avg_ms'] if report['ocr']['all'] else 0
        
        # ORB 匹配结果
        orb_results = report.get('orb', {})
        orb_large_ms = orb_results.get('Large', {}).get('time_ms', 0)
        orb_medium_ms = orb_results.get('Medium', {}).get('time_ms', 0)
        orb_small_ms = orb_results.get('Small', {}).get('time_ms', 0)
        
        ConfigManager().save({
            "preferred_provider": yolo_provider,
            "best_ocr": ocr_engine
        })
        
        # 显示详细的配置信息（用人话）
        title = "✅ 环境配置完成"
        content = (
            f"<b>视觉识别引擎：</b>{yolo_provider}<br>"
            f"<span style='color:#888;'>→ 单帧耗时：{yolo_avg_ms:.1f} 毫秒 | 建议帧率：{yolo_fps} FPS</span><br><br>"
            f"<b>图片匹配性能：</b>ORB 特征匹配<br>"
            f"<span style='color:#888;'>→ 大型卡牌：{orb_large_ms:.0f} 毫秒 | "
            f"中型卡牌：{orb_medium_ms:.0f} 毫秒 | "
            f"小型卡牌：{orb_small_ms:.0f} 毫秒</span><br><br>"
            f"<b>文字识别引擎：</b>{ocr_engine}<br>"
            f"<span style='color:#888;'>→ 识别耗时：{ocr_avg_ms:.0f} 毫秒</span><br><br>"
            f"<span style='color:#3fb950;'>系统已自动选择最佳配置，您可以直接开始使用！</span>"
        )
        
        self.result_card.set_info(title, content)
        self.result_card.show()

    def mousePressEvent(self, event):
        """鼠标按下事件 - 记录拖动起始位置"""
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 实现窗口拖动"""
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            
    def _on_enter_main(self):
        """进入主界面按钮"""
        self.enter_main_requested.emit()
        self.hide()
        
    def _on_close(self):
        """关闭窗口"""
        self.closed.emit()
        self.hide()