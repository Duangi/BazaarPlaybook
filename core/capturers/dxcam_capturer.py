import sys
import numpy as np
from loguru import logger
from .base import BaseCapturer

# dxcam 仅在 Windows 上可用
if sys.platform == "win32":
    try:
        import dxcam
    except ImportError:
        dxcam = None
        logger.warning("dxcam not available on this platform")
else:
    dxcam = None

class DXCamCapturer(BaseCapturer):
    def __init__(self, target_fps=30):
        super().__init__()
        self.camera = None
        self.target_fps = target_fps
        
        if dxcam is None:
            logger.error("DXCam is not available on this platform (Windows only)")
            return
        
        try:
            # create(device_idx=0, output_idx=0) - 默认主显示器
            self.camera = dxcam.create(output_idx=0, output_color="BGR")
            logger.info("DXCam capturer initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize DXCam: {e}")
            self.camera = None

    def capture(self) -> np.ndarray:
        if not self.camera:
            return None
        
        # start/stop mechanism or grab? grab is better for on-demand
        try:
            # grab returns None if no new frame is available sometimes, but here we want a frame.
            # Convert region from (x, y, w, h) to (l, t, r, b)
            region = None
            if self.region:
                x, y, w, h = self.region
                # Clamp to screen bounds to prevent Invalid Region error
                if self.camera:
                    screen_w, screen_h = self.camera.width, self.camera.height
                    x = max(0, x)
                    y = max(0, y)
                    # Enforce right/bottom bounds
                    r = min(x + w, screen_w)
                    b = min(y + h, screen_h)
                    
                    # If valid area
                    if r > x and b > y:
                        region = (x, y, r, b)
                    else:
                        # Region is completely out of bounds or invalid
                        return None
                else:
                    region = (x, y, x + w, y + h)

            frame = self.camera.grab(region=region)
            return frame
        except Exception as e:
            logger.warning(f"DXCam capture failed: {e}")
            return None

    def release(self):
        if self.camera:
            self.camera.stop()
            del self.camera
            self.camera = None
