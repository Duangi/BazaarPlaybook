import cv2
import time
import onnxruntime as ort
from loguru import logger
import config
from core.detectors.yolo_detector import YoloDetector
from platforms.adapter import PlatformAdapter
from utils.search_engine import FuzzySearcher

def main():
    logger.info("=== 启动插件性能深度诊断 (All-in-One Benchmark) ===")
    
    test_img_path = "tests/assets/detail/detail_1.png"
    frame = cv2.imread(test_img_path)
    searcher = FuzzySearcher(config.ITEMS_DB_PATH)
    
    # ============================================================
    # 1. YOLO Provider 全量性能测试
    # ============================================================
    logger.info("正在探测所有可用的 ONNX Providers...")
    all_providers = ort.get_available_providers()
    yolo_results = []

    for provider in all_providers:
        logger.info(f"测试 YOLO 运行环境: {provider}")
        try:
            # 强制指定当前测试的 Provider
            start_load = time.perf_counter()
            # 这里需要你的 YoloDetector 支持传入 provider，或者我们直接在这里操作 session
            session = ort.InferenceSession(config.MODEL_PATH, providers=[provider])
            load_time = (time.perf_counter() - start_load) * 1000

            # 推理热身 (消除首次运行波动)
            input_name = session.get_inputs()[0].name
            # 简单模拟输入
            blob = cv2.resize(frame, (640, 640)).transpose(2, 0, 1)[None, ...].astype('float32') / 255.0
            session.run(None, {input_name: blob})

            # 正式测速 (跑 5 次取平均)
            inf_times = []
            for _ in range(5):
                t_s = time.perf_counter()
                session.run(None, {input_name: blob})
                inf_times.append((time.perf_counter() - t_s) * 1000)
            
            avg_inf = sum(inf_times) / len(inf_times)
            yolo_results.append({
                "provider": provider,
                "load_ms": load_time,
                "inf_ms": avg_inf
            })
        except Exception as e:
            logger.error(f"Provider {provider} 启动失败: {e}")

    # ============================================================
    # 2. OCR 引擎全量准确率/速度测试
    # ============================================================
    logger.info("正在测试所有 OCR 引擎...")
    engines = PlatformAdapter.get_all_ocr_engines()
    
    # 预先拿到详情框
    detector = YoloDetector(config.MODEL_PATH)
    dets = detector.detect_stream(frame)
    detail_dets = [d for d in dets if int(d['class_id']) == config.CLS_MAP['DETAIL']]
    
    ocr_results = []
    if detail_dets:
        x, y, w, h = detail_dets[0]['box']
        # 为了公平，切取上半部分
        detail_crop = frame[y:y+int(h*0.45), x:x+w]

        for engine in engines:
            logger.info(f"正在运行引擎测试: {engine.name}")
            # 同样测试 3 次
            times = []
            final_id = "None"
            raw_text = ""
            for i in range(3):
                t_s = time.perf_counter()
                raw_text = engine.recognize(detail_crop)
                times.append((time.perf_counter() - t_s) * 1000)
                
                # 模糊匹配
                clean_text = raw_text.split("\n")[0].replace(" ", "")
                final_id = searcher.find_best_match(clean_text) or "Failed"

            ocr_results.append({
                "name": engine.name,
                "first_ms": times[0],
                "avg_ms": sum(times) / len(times),
                "text": raw_text.replace("\n", " ").strip()[:10],
                "id": final_id
            })

    # ============================================================
    # 3. 汇总打印 (解决标题对不齐问题)
    # ============================================================
    print("\n" + "="*85)
    print(f"{'YOLO Provider对比':<30} | {'加载耗时(ms)':<15} | {'平均推理(ms)':<15}")
    print("-" * 85)
    for r in yolo_results:
        print(f"{r['provider']:<30} | {r['load_ms']:14.2f} | {r['inf_ms']:14.2f}")

    print("\n" + "="*85)
    print(f"{'OCR 引擎对比':<20} | {'首次(ms)':<10} | {'稳态平均(ms)':<12} | {'文本预览':<10} | {'结果'}")
    print("-" * 85)
    for r in ocr_results:
        print(f"{r['name']:<20} | {r['first_ms']:9.2f} | {r['avg_ms']:11.2f} | {r['text']:<10} | {r['id']}")
    print("="*85 + "\n")

if __name__ == "__main__":
    main()