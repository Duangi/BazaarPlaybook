import sys
from platforms.interfaces.ocr import OCREngine
from platforms.interfaces.window import WindowManager
from loguru import logger

class PlatformAdapter:
    """
    平台适配器：负责屏蔽操作系统差异，提供标准化的底层能力。
    """

    @staticmethod
    def get_ocr_engine() -> OCREngine:
        """
        根据当前操作系统，获取对应的 OCR 引擎实现
        """
        if sys.platform == "win32":
            try:
                from platforms.windows.ocr import WindowsOCREngine
                win_engine = WindowsOCREngine()
                
                # 如果 Windows 原生引擎可用，直接返回
                if win_engine.is_available():
                    return win_engine
                else:
                    logger.warning("Windows 原生 OCR 初始化失败，准备回退到 RapidOCR...")
            except Exception as e:
                logger.error(f"加载 Windows OCR 模块出错: {e}，准备回退...")

            
        
        elif sys.platform == "darwin":
            # 预留给 Mac
            # from .macos.ocr_engine import MacOSOCREngine
            # return MacOSOCREngine()
            pass
        
        try:
            from platforms.common.ocr import CommonOCREngine
            logger.info("已成功激活 RapidOCR 通用引擎")
            return CommonOCREngine()
        except Exception as e:
            logger.error(f"所有 OCR 引擎均不可用! 错误原因: {e}")
            # 如果连 RapidOCR 都没装，这里可以返回一个空的 NullEngine 防止崩溃
            from platforms.interfaces.ocr import NullOCREngine
            return NullOCREngine()

    @staticmethod
    def get_all_ocr_engines() -> list[OCREngine]:
        """【探测模式】获取系统当前所有可用的 OCR 引擎"""
        available_engines = []

        # 1. 尝试加载 Windows 原生引擎
        if sys.platform == "win32":
            try:
                from platforms.windows.ocr import WindowsOCREngine
                win_engine = WindowsOCREngine()
                if win_engine.is_available():
                    # 我们给引擎贴个标签，方便测试脚本识别
                    win_engine.name = "Windows_Native"
                    available_engines.append(win_engine)
            except Exception as e:
                logger.debug(f"Windows Native OCR 不可用: {e}")

        # 2. 尝试加载通用引擎 (RapidOCR)
        try:
            from platforms.common.ocr import CommonOCREngine
            gen_engine = CommonOCREngine()
            gen_engine.name = "RapidOCR_ONNX"
            available_engines.append(gen_engine)
        except Exception as e:
            logger.debug(f"RapidOCR 引擎不可用: {e}")

        # 3. 可以在这里继续添加其它引擎，比如 EasyOCR 或 Tesseract
        
        return available_engines
    
    @staticmethod
    def get_window_manager() -> WindowManager:
        """
        根据当前操作系统，获取对应的窗口管理器实现
        """
        if sys.platform == "win32":
            try:
                from platforms.windows.window import WindowsWindowManager
                return WindowsWindowManager()
            except Exception as e:
                logger.error(f"加载 Windows 窗口管理器失败: {e}")
        
        elif sys.platform == "darwin":
            try:
                from platforms.macos.window import MacOSWindowManager
                return MacOSWindowManager()
            except Exception as e:
                logger.error(f"加载 macOS 窗口管理器失败: {e}")
        
        elif sys.platform.startswith("linux"):
            try:
                from platforms.linux.window import LinuxWindowManager
                return LinuxWindowManager()
            except Exception as e:
                logger.error(f"加载 Linux 窗口管理器失败: {e}")
        
        # 回退到空实现
        logger.warning("当前平台不支持窗口管理，使用空实现")
        from platforms.interfaces.window import NullWindowManager
        return NullWindowManager()
    
    @staticmethod
    def get_capture_tool():
        """
        预留：获取截图工具
        """
        pass