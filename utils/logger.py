import sys
from loguru import logger

def setup_logger():
    """
    配置全局 Loguru 日志记录器。

    将日志同时输出到控制台和文件中。
    - 控制台: INFO 级别以上，格式简洁。
    - 文件: DEBUG 级别以上，记录在 logs/app.log，格式详细，带模块和行号。
    """
    logger.remove()  # 移除默认的 handler，以便自定义

    # 控制台输出配置
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        colorize=True
    )

    # 文件输出配置
    logger.add(
        "logs/app.log",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",  # 每 10 MB 切割一个新文件
        retention="7 days", # 最多保留 7 天的日志
        encoding="utf-8",
        enqueue=True,      # 异步写入，防止阻塞
        backtrace=True,    # 记录完整的异常堆栈
        diagnose=True
    )

    logger.info("日志系统初始化完成。")

# 立即执行，以便其他模块导入时日志系统已经配置好
setup_logger()
