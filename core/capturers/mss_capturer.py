import mss
import numpy as np
import cv2
from .base import BaseCapturer
from loguru import logger

class MSSCapturer(BaseCapturer):
    def __init__(self):
        super().__init__()
        self.sct = mss.mss()
        logger.info("MSS capturer initialized.")

    def capture(self) -> np.ndarray:
        if not self.region:
            monitor = self.sct.monitors[1] # Default to primary
        else:
            # MSS region: {'top': 100, 'left': 200, 'width': 300, 'height': 400}
            monitor = {
                "top": self.region[1],
                "left": self.region[0],
                "width": self.region[2],
                "height": self.region[3]
            }
        
        try:
            img = self.sct.grab(monitor)
            # Convert to numpy array (BGRA -> BGR)
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            return frame
        except Exception as e:
            logger.warning(f"MSS capture failed: {e}")
            return None
