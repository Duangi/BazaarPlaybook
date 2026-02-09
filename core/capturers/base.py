from abc import ABC, abstractmethod
import numpy as np
from typing import Tuple, Optional

class BaseCapturer(ABC):
    """
    屏幕截图基类
    """
    def __init__(self):
        self.region: Optional[Tuple[int, int, int, int]] = None  # (left, top, width, height)

    def set_region(self, region: Tuple[int, int, int, int]):
        """
        设置截图区域
        :param region: (left, top, width, height)
        """
        self.region = region

    @abstractmethod
    def capture(self) -> Optional[np.ndarray]:
        """
        获取截图
        :return: numpy array (H, W, C) in RGB or BGR format, or None on failure
        """
        pass
