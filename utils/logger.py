# utils/logger.py
import sys
import os
from loguru import logger
from PySide6.QtCore import QCoreApplication, QObject, Signal, QMetaObject, Qt
try:
    from PySide6.QtWidgets import QTextEdit
    from PySide6.QtGui import QTextCursor, QColor
except ImportError:
    # 如果在非GUI环境运行（比如测试脚本）
    QTextEdit = None
    QTextCursor = None
    QColor = None

# 确保 logs 文件夹存在
if not os.path.exists("logs"):
    os.makedirs("logs", exist_ok=True)

# 基础配置
LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:<8}</level> | <cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
FILE_ROTATION = "10 MB"
RETENTION = "7 days"

# 🔥 Qt日志处理器（用于在GUI中显示日志）
class QtLogHandler(QObject):
    """将loguru日志输出到QTextEdit的Handler"""
    log_signal = Signal(str, str)  # (level, message)
    
    def __init__(self, text_edit: QTextEdit):
        super().__init__()
        self.text_edit = text_edit
        self.log_signal.connect(self._append_log, Qt.ConnectionType.QueuedConnection)
        
        # 日志级别颜色映射
        self.level_colors = {
            "TRACE": "#6c757d",
            "DEBUG": "#17a2b8",
            "INFO": "#28a745",     # 绿色
            "SUCCESS": "#00d26a",  # 亮绿色
            "WARNING": "#ffc107",  # 黄色
            "ERROR": "#dc3545",    # 红色
            "CRITICAL": "#e83e8c"  # 粉红色
        }
    
    def write(self, message: str):
        """loguru调用的写入方法"""
        # 解析日志级别（从格式化后的消息中提取）
        level = "INFO"
        if "DEBUG" in message:
            level = "DEBUG"
        elif "WARNING" in message or "WARN" in message:
            level = "WARNING"
        elif "ERROR" in message:
            level = "ERROR"
        elif "SUCCESS" in message:
            level = "SUCCESS"
        elif "CRITICAL" in message:
            level = "CRITICAL"
        
        self.log_signal.emit(level, message)
    
    def _append_log(self, level: str, message: str):
        """在QTextEdit中追加日志（带颜色）"""
        if not self.text_edit or self.text_edit.isHidden():
            return
        
        color = self.level_colors.get(level, "#c0c0c0")
        
        # 移除ANSI转义码（loguru的彩色输出）
        import re
        clean_message = re.sub(r'\x1b\[[0-9;]*m', '', message)
        
        # 添加HTML格式的日志
        html = f'<span style="color: {color};">{clean_message}</span><br>'
        
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.text_edit.setTextCursor(cursor)
        self.text_edit.insertHtml(html)
        
        # 自动滚动到底部
        try:
            scrollbar = self.text_edit.verticalScrollBar()
            if scrollbar:
                scrollbar.setValue(scrollbar.maximum())
        except:
            pass
    
    def flush(self):
        """刷新（loguru要求）"""
        pass

# 全局handler引用（防止被垃圾回收）
_qt_handler = None

def add_qt_log_handler(text_edit, debug_mode: bool = False):
    """添加Qt日志处理器到loguru"""
    if QTextEdit is None or text_edit is None:
        return  # Qt组件未加载或text_edit为None
    
    global _qt_handler
    
    # 移除旧的Qt handler
    if _qt_handler:
        try:
            logger.remove(_qt_handler.handler_id)
        except:
            pass
    
    # 创建新handler
    _qt_handler = QtLogHandler(text_edit)
    
    # 根据debug模式设置级别
    level = "DEBUG" if debug_mode else "INFO"
    
    # 添加到loguru
    handler_id = logger.add(
        _qt_handler.write,
        format="{time:HH:mm:ss} | {level:<7} | {message}",
        level=level,
        colorize=False  # Qt端我们自己处理颜色
    )
    _qt_handler.handler_id = handler_id


def setup_logger(is_gui_app: bool = True, debug_mode: bool = False):
    """
    配置日志输出。
    :param is_gui_app: 是否为 GUI 应用 (默认为 True，控制台只输出 INFO)
    :param debug_mode: 是否强制开启调试模式 (若为 True，控制台输出 DEBUG)
    """
    logger.remove() # 清除默认配置

    # --- Console Handler ---
    # 如果是 GUI 应用且未开启调试模式，只显示 INFO
    # 如果是非 GUI 应用 (如测试) 或者 强制开启调试模式，显示 DEBUG
    console_level = "WARNING" if is_gui_app and not debug_mode else "DEBUG"
    
    # 稍微调整控制台输出格式，使其更紧凑
    console_format = "<green>{time:HH:mm:ss}</green> | <level>{level: <7}</level> | <cyan>{module}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

    logger.add(sys.stderr, format=console_format, level=console_level, colorize=True, backtrace=True, diagnose=True)

    # --- File Handler ---
    # 总是输出 DEBUG 及以上到文件，方便调试
    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log", 
        rotation=FILE_ROTATION, 
        retention=RETENTION, 
        level="DEBUG", 
        format=LOG_FORMAT,
        colorize=False, # 文件日志不需要颜色
        backtrace=True, 
        diagnose=True
    )
    
    if debug_mode:
        logger.info("🔧 调试模式已开启 (Debug Mode Enabled)")

    logger.info("日志系统配置完成。")
    # 记录运行环境信息
    logger.debug(f"Python Interpreter: {sys.executable}")
    logger.debug(f"Python Version: {sys.version}")
    
    try:
        # 检查是否是 GUI 应用（由 main.py 启动）
        QCoreApplication.instance()
        logger.debug("检测到 GUI 环境 (QApplication.instance() 存在)")
    except RuntimeError:
        logger.debug("非 GUI 环境 (可能是 CLI 脚本)")

    return logger

# 在你的 main.py 中调用：
# from utils.logger import setup_logger
# logger = setup_logger(is_gui_app=True) # 传入 True