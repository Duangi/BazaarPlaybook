import sys
import os
import cv2
import time
import numpy as np
import ctypes
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.capturers.dxcam_capturer import DXCamCapturer
from utils.window_utils import get_window_rect

def set_dpi_awareness():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1) # PROCESS_SYSTEM_DPI_AWARE
        logger.info("DPI Awareness set to System DPI Aware")
    except Exception as e:
        logger.warning(f"Failed to set DPI awareness: {e}")

def test_capture():
    set_dpi_awareness()
    logger.info("Starting capture test...")
    
    # Debug DXCam outputs
    import dxcam
    logger.info(f"DXCam Device Info: {dxcam.device_info()}")
    # Try capturing full screen first without region to see if we get black screen
    capturer = DXCamCapturer()
    if capturer.camera:
        logger.info(f"Monitor Resolution: {capturer.camera.width}x{capturer.camera.height}")
    
    # 1. Try to find the game window
    game_title = "The Bazaar"
    rect = get_window_rect(game_title)
    
    if not rect:
        logger.warning(f"Window '{game_title}' not found. Testing with full screen.")
        if capturer.camera:
            rect = (0, 0, capturer.camera.width, capturer.camera.height)
        else:
            rect = (0, 0, 1920, 1080)
    else:
        logger.info(f"Found '{game_title}' at: {rect} (x, y, w, h)")

    if not capturer.camera:
        logger.error("Failed to initialize DXCam.")
        return

    # 3. Set Region
    capturer.set_region(rect)
    
    # 4. Capture
    logger.info("Attempting capture...")
    start_time = time.time()
    frame = capturer.capture()
    end_time = time.time()
    
    if frame is not None:
        if np.mean(frame) < 5:
            logger.warning("Capture seems to be mostly black/dark!")
        
        logger.success(f"Capture successful! Shape: {frame.shape}, Time: {(end_time - start_time)*1000:.2f}ms")
        
        # 5. Save verification image
        save_path = os.path.join("assets", "debug", "test_capture_v2.png")
        cv2.imwrite(save_path, frame)
        logger.info(f"Saved capture to: {save_path}")
    else:
        logger.error("Capture returned None.")

if __name__ == "__main__":
    test_capture()
