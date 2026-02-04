import time
import json
import cv2
from loguru import logger
import config
from core.detectors.yolo_detector import YoloDetector
from core.comparators.feature_matcher import FeatureMatcher

def get_card_size_by_ratio(w, h):
    """
    完全复刻 Rust 版宽高比判断逻辑:
    中型 (Medium): 0.85 <= ratio <= 1.15
    大型 (Large): ratio > 1.15
    小型 (Small): ratio < 0.85
    """
    aspect_ratio = float(w) / float(h)
    
    if 0.85 <= aspect_ratio <= 1.15:
        return "Medium"
    elif aspect_ratio > 1.15:
        return "Large"
    else:
        return "Small"

def main():
    logger.info("启动 [宽高比逻辑] 基准测试...")
    
    yolo = YoloDetector(config.MODEL_PATH)
    matcher = FeatureMatcher()
    
    with open(config.ITEMS_DB_PATH, 'r', encoding='utf-8') as f:
        id_map = {i['id']: i['name_cn'] for i in json.load(f)}

    img = cv2.imread("tests/assets/Jules1.png")
    if img is None: 
        return

    results = yolo.detect_stream(img)
    item_dets = [d for d in results if d['class_id'] == config.CLS_MAP['ITEM']]
    
    logger.info(f"找到 {len(item_dets)} 个卡牌目标。")

    for i, det in enumerate(item_dets):
        x, y, w, h = det['box']
        
        # 使用旧版 Rust 比例逻辑
        size_cat = get_card_size_by_ratio(w, h)
        
        crop = img[y:y+h, x:x+w]

        t_s = time.perf_counter()
        res = matcher.match(crop, size_cat)
        duration = (time.perf_counter() - t_s) * 1000
        
        if res:
            best_id, score = res[0]
            name = id_map.get(best_id, "未知")
            logger.info(f"目标 {i+1} | 形状: {size_cat:<7} | 匹配: {name:<10} | 得分: {score:.4f} | 耗时: {duration:.1f}ms")
        else:
            # 如果匹配失败，打印一下当前的比例，方便调试
            ratio = w/h
            logger.warning(f"目标 {i+1} 匹配失败 | 形状: {size_cat} (ratio:{ratio:.2f}) | 无匹配或分数过低")

if __name__ == "__main__":
    main()