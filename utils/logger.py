# utils/logger.py
import sys
import os
from loguru import logger
from PySide6.QtCore import QCoreApplication # 用于检查是否是 GUI 应用

# 确保 logs 文件夹存在
if not os.path.exists("logs"):
    os.makedirs("logs", exist_ok=True)

# 基础配置
LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:<8}</level> | <cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
FILE_ROTATION = "10 MB"
RETENTION = "7 days"

def setup_logger(is_gui_app: bool = True):
    """
    配置日志输出。
    - GUI 应用 (运行时): 只输出 INFO 及以上到控制台，DEBUG 到文件。
    - 非 GUI (如测试脚本): 输出 DEBUG 及以上到控制台和文件。
    """
    logger.remove() # 清除默认配置

    # --- Console Handler ---
    console_level = "INFO"
    if not is_gui_app:
        console_level = "DEBUG" # 开发测试时，控制台输出更详细

    logger.add(sys.stderr, format=LOG_FORMAT, level=console_level, colorize=True, backtrace=True, diagnose=True)

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