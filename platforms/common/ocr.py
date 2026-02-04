from rapidocr_onnxruntime import RapidOCR
from platforms.interfaces.ocr import OCREngine
from loguru import logger

class CommonOCREngine(OCREngine):
    def __init__(self):
        try:
            # 初始化 RapidOCR 引擎
            # 第一次运行会自动下载模型 (约 10MB)
            self._engine = RapidOCR()
            logger.info("RapidOCR 引擎准备就绪")
        except Exception as e:
            logger.error(f"RapidOCR 引擎初始化失败: {e}")
            self._engine = None

    def is_available(self) -> bool:
        """检查 OCR 引擎是否可用"""
        return self._engine is not None

    def recognize(self, image) -> str:
        # 1. 直接调用 RapidOCR
        result, _ = self._engine(image)
        if not result:
            return ""
        
        # 2. 按照 Y 坐标排序并拼接成标准格式返回
        # 这样 business layer (OCRService) 拿到的数据格式就统一了
        result.sort(key=lambda x: x[0][0][1])
        return "\n".join([line[1] for line in result])