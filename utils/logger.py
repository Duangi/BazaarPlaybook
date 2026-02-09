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