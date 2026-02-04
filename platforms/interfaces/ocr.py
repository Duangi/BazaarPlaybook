from abc import ABC, abstractmethod
import numpy as np

class OCREngine(ABC):
    name = "BaseOCR"
    @abstractmethod
    def recognize(self, image: np.ndarray) -> str:
        """
        执行文字识别任务
        :param image: OpenCV 格式的图像 (numpy array)
        :return: 识别出的原始文本内容
        """
        pass

class NullOCREngine(OCREngine):
    name = "NullOCR"
    """一个空的 OCR 引擎实现，始终返回空字符串。防止系统崩溃。"""
    def recognize(self, image: np.ndarray) -> str:
        return ""