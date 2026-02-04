import cv2
import time
from loguru import logger
import config
from core.detectors.yolo_detector import YoloDetector
from platforms.adapter import PlatformAdapter
from utils.search_engine import FuzzySearcher

def main():
    logger.info("=== 启动 OCR 多引擎对比测试 ===")

    # 1. 初始化
    yolo = YoloDetector(config.MODEL_PATH)
    searcher = FuzzySearcher(config.ITEMS_DB_PATH)
    
    # 2. 获取所有可用引擎
    engines = PlatformAdapter.get_all_ocr_engines()
    logger.info(f"适配器共提供 {len(engines)} 个可用引擎")

    img = cv2.imread("tests/assets/detail/detail_1.png")
    results = yolo.detect_stream(img)
    detail_dets = [d for d in results if int(d['class_id']) == config.CLS_MAP['DETAIL']]

    if not detail_dets: 
        return

    # 3. 交叉比对
    det = detail_dets[0]
    x, y, w, h = det['box']
    detail_crop = img[y:y+h, x:x+w]

    print(f"\n{'引擎名称':<20} | {'耗时(ms)':<10} | {'识别结果':<15} | {'匹配ID'}")
    print("-" * 80)

    for engine in engines:
        # 每个引擎跑 3 次取平均值，排除干扰
        times = []
        last_id = "None"
        
        for _ in range(3):
            start = time.perf_counter()
            raw_text = engine.recognize(detail_crop)
            times.append((time.perf_counter() - start) * 1000)
            
            # 处理文字并匹配
            first_line = raw_text.split("\n")[0].replace(" ", "")
            last_id = searcher.find_best_match(first_line) or "Failed"

        avg_time = sum(times) / len(times)
        # 取最后一次的 raw_text 缩略显示
        text_preview = raw_text.split("\n")[0][:10]
        
        print(f"{engine.name:<20} | {avg_time:10.2f} | {text_preview:<15} | {last_id}")

if __name__ == "__main__":
    main()