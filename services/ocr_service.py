import cv2
from loguru import logger
import config
from utils.search_engine import FuzzySearcher
from platforms.adapter import PlatformAdapter

class OCRService:
    def __init__(self, db_path):
        """
        初始化 OCR 服务
        :param db_path: items_db.json 的路径
        """
        try:
            # 初始化 OCR 引擎
            self.engine = PlatformAdapter.get_ocr_engine()
            
            # 初始化独立的模糊匹配引擎
            self.searcher = FuzzySearcher(db_path)
            
            logger.success("OCRService 初始化成功 (使用 RapidOCR + FuzzySearcher)")
        except Exception as e:
            logger.error(f"OCRService 初始化失败: {e}")

    def _preprocess_for_ocr(self, img):
        """
        针对游戏详情框进行图像预处理
        自适应二值化：无论背景是深棕色还是黑色，文字是金色还是白色，都能转为黑底白字。
        """
        # 1. 转为灰度图
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 2. 图像放大：OCR 对大尺寸文字更准 (尤其是分辨率低时)
        # 建议放大 1.5 - 2 倍
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        
        # 3. 自适应二值化 (Adaptive Thresholding)
        # ADAPTIVE_THRESH_GAUSSIAN_C 效果通常比平均值法更好
        # blockSize 必须为奇数，值越大对光影分布的鲁棒性越好
        binary = cv2.adaptiveThreshold(
            gray, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 
            11, 2
        )
        
        # 4. 可选：反色。OCR 引擎通常喜欢白底黑字或黑底白字。
        # RapidOCR 对黑白对比度敏感，我们确保文字是亮的
        return binary

    def recognize_card_id(self, detail_crop):
        if detail_crop is None or detail_crop.size == 0:
            return None

        try:
            # 1. 这里的 raw_text 已经是一个字符串了，例如 "港口\n费：3"
            raw_text = self.engine.recognize(detail_crop)

            if not raw_text:
                return None

            # 2. 直接按行切分
            lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
            
            if not lines:
                return None

            # 3. 拿到第一行（也就是详情框最顶部的文字）
            first_line = lines[0]

            clean_name = first_line.replace(" ", "")  # 去掉空格，防止 OCR 识别出多余空格影响匹配
            logger.info(f"🔍 OCR 确权目标文字: '{clean_name}' (原始: '{first_line}')")
            # 4. 执行模糊匹配
            return self.searcher.find_best_match(clean_name, threshold=config.FUZZY_MATCH_THRESHOLD)

        except Exception as e:
            logger.error(f"OCRService 业务逻辑报错: {e}")
            import traceback
            logger.error(traceback.format_exc()) # 打印详细堆栈方便定位
            return None

    def debug_save_ocr_step(self, detail_crop, filename="logs/ocr_debug.png"):
        """ 调试用：保存预处理后的图片，看看 OCR 引擎到底看到了什么 """
        processed = self._preprocess_for_ocr(detail_crop)
        cv2.imwrite(filename, processed)
        logger.debug(f"已保存 OCR 预处理调试图至: {filename}")