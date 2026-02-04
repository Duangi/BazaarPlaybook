import cv2
import json
from rapidocr_onnxruntime import RapidOCR
from rapidfuzz import process, fuzz
from loguru import logger
import config

class OCRService:
    def __init__(self, items_db_path):
        self.engine = RapidOCR()
        with open(items_db_path, 'r', encoding='utf-8') as f:
            self.items_db = json.load(f)
            
        self.name_to_id = {item['name_cn']: item['id'] for item in self.items_db}
        self.all_names = list(self.name_to_id.keys())

    def _preprocess(self, img):
        """ 全局自适应预处理 """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # 针对不同颜色的背景，自适应二值化是万能的
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        return binary

    def recognize_name(self, detail_crop):
        """ 
        全框扫描逻辑：
        1. 对整个 YOLO 截取的 detail 框进行 OCR
        2. 寻找位置最靠上的文字块
        3. 处理前缀并匹配数据库
        """
        # 预处理整个详情框
        processed = self._preprocess(detail_crop)
        
        # OCR 识别全框内容
        # RapidOCR 会返回每个文字块的 [坐标, 文本, 置信度]
        results, _ = self.engine(processed)
        
        if not results:
            return None

        # 1. 过滤：只保留位于框的上半部分（前 40% 高度）的文字块
        # 因为详情框底部可能有很长的描述，我们要的名字肯定在上面
        h_limit = detail_crop.shape[0] * 0.4
        top_candidates = []
        
        for res in results:
            box, text, conf = res
            top_left_y = box[0][1] # 文字块左上角的 Y 坐标
            if top_left_y < h_limit:
                top_candidates.append((top_left_y, text))
        
        if not top_candidates:
            return None

        # 2. 排序：取 Y 坐标最小（最靠上）的一行
        top_candidates.sort(key=lambda x: x[0])
        raw_text = top_candidates[0][1].strip()
        
        logger.info(f"✨ 详情框顶部文字抓取成功: {raw_text}")

        # 3. 匹配与去前缀逻辑
        # 针对 "沉重 农贸集市"、"一发入魂" 这种不同情况
        best_match = self._fuzzy_match_name(raw_text)
        
        return best_match

    def _fuzzy_match_name(self, raw_text):
        """ 针对附魔前缀的增强匹配逻辑 """
        # A. 尝试直接匹配（应对没有前缀的情况，如 "一发入魂"）
        res = process.extractOne(raw_text, self.all_names, scorer=fuzz.WRatio)
        
        # B. 尝试分词匹配（应对有前缀的情况，如 "沉重 农贸集市"）
        # 游戏里通常前缀和名字之间有空格，或者名字在最后
        parts = raw_text.split(" ")
        if len(parts) > 1:
            # 优先尝试最后一个词（真正的卡牌名）
            sub_res = process.extractOne(parts[-1], self.all_names, scorer=fuzz.WRatio)
            if sub_res[1] > res[1]:
                res = sub_res
                
        if res and res[1] >= config.FUZZY_MATCH_THRESHOLD:
            logger.success(f"🤝 匹配到 ID: {self.name_to_id[res[0]]} (名字: {res[0]})")
            return self.name_to_id[res[0]]
            
        return None