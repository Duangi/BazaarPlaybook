# platforms/windows/ocr_engine.py
import asyncio
import cv2
from loguru import logger
import numpy as np
from platforms.interfaces.ocr import OCREngine

class WindowsOCREngine(OCREngine):
    def __init__(self):
        try:
            from winsdk.windows.media.ocr import OcrEngine
            from winsdk.windows.graphics.imaging import BitmapDecoder
            from winsdk.windows.storage.streams import DataWriter, InMemoryRandomAccessStream
            
            self._engine = OcrEngine.try_create_from_user_profile_languages()
            self._BitmapDecoder = BitmapDecoder
            self._DataWriter = DataWriter
            self._InMemoryRandomAccessStream = InMemoryRandomAccessStream

            if self._engine is None:
                logger.error("Windows OCR 引擎在当前系统不可用 (可能是精简版系统)")

            logger.info("Windows Native OCR Engine 准备就绪")
        except ImportError:
            self._engine = None

    def is_available(self) -> bool:
        """检查 OCR 引擎是否可用"""
        return self._engine is not None

    def recognize(self, image: np.ndarray) -> str:
        if self._engine is None: 
            return ""
        # 同步包装异步
        return asyncio.run(self._do_recognize(image))

    async def _do_recognize(self, cv2_img) -> str:
        try:
            # OpenCV -> SoftwareBitmap 转换过程
            success, buffer = cv2.imencode('.bmp', cv2_img)
            if not success: 
                return ""
            
            stream = self._InMemoryRandomAccessStream()

            writer = self._DataWriter(stream)
            writer.write_bytes(buffer.tobytes())
            await writer.store_async()
            stream.seek(0)
            
            decoder = await self._BitmapDecoder.create_async(stream)
            bitmap = await decoder.get_software_bitmap_async()
            
            # 识别
            result = await self._engine.recognize_async(bitmap)
            return "\n".join([line.text for line in result.lines])
        except Exception as e:
            logger.error(f"Windows OCR 识别失败: {e}")
            return ""