import time
import numpy as np
import onnxruntime as ort
import cv2
import os
from loguru import logger

import config
from core.detectors.yolo_detector import YoloDetector
from core.comparators.feature_matcher import FeatureMatcher
from platforms.adapter import PlatformAdapter

class SystemDiagnostics:
    def __init__(self):
        logger.info("Diag: 正在初始化诊断引擎...")
        self.adapter = PlatformAdapter()

    def benchmark_yolo(self, image_path):
        """任务1：测试所有可用 Provider 的推理速度"""
        logger.info(f"Diag: 开始运行 YOLO 性能测试 (图片: {image_path})")
        
        if not os.path.exists(image_path):
            logger.error(f"Diag: 测试图片不存在: {image_path}")
            return None

        img = cv2.imread(image_path)
        if img is None:
            logger.error("Diag: 图片解码失败")
            return None

        providers = ort.get_available_providers()
        results = []

        for p in providers:
            logger.info(f"Diag: 正在评估后端 -> {p}")
            try:
                # 实例化真正的类，触发其内部的初始化日志
                detector = YoloDetector(config.MODEL_PATH, providers=[p])
                
                # 预热一次
                detector.detect_stream(img)
                
                # 计时测试
                times = []
                for i in range(15):
                    start = time.perf_counter()
                    detector.detect_stream(img) # 触发 yolo_detector.py 内部的剖析日志
                    times.append((time.perf_counter() - start) * 1000)
                
                avg_ms = np.mean(times)
                results.append({"provider": p, "avg_ms": avg_ms})
                logger.success(f"Diag: {p} 测试完成，平均耗时: {avg_ms:.2f}ms")
            except Exception as e:
                logger.warning(f"Diag: Provider {p} 启动或运行失败: {e}")
                continue

        if not results:
            return None

        best = min(results, key=lambda x: x['avg_ms'])
        suggested_fps = int(1000 / (best['avg_ms'] * 1.5))
        return {
            "best_provider": best['provider'], 
            "avg_ms": best['avg_ms'], 
            "suggested_fps": min(suggested_fps, 30), 
            "all": results
        }

    def benchmark_matcher(self, image_samples: dict):
        """任务2：测试 ORB 在不同尺寸下的耗时"""
        logger.info("Diag: 开始运行 ORB 匹配深度测试...")
        # 实例化真正的类，触发其库加载日志
        matcher = FeatureMatcher()
        report = {}
        
        for size, img in image_samples.items():
            if img is None:
                logger.warning(f"Diag: 跳过 {size} 样本测试，图像数据为空")
                continue
            
            logger.info(f"Diag: 正在比对 {size} 分类样本...")
            start = time.perf_counter()
            res = matcher.match(img, size) # 触发 feature_matcher.py 内部的匹配日志
            dur = (time.perf_counter() - start) * 1000
            
            score = res[0][1] if res else 0.0
            matched_id = res[0][0] if res else None
            
            report[size] = {"time_ms": dur, "matched": matched_id, "score": score}
            
        return report

    def benchmark_ocr(self, detail_img):
        """任务3：测试所有 OCR 引擎速度并选择最快"""
        logger.info("Diag: 开始运行 OCR 引擎全量对比测试...")
        
        if detail_img is None:
            logger.error("Diag: 传入的 OCR 测试图片为 None，请检查路径！")
            return None

        engines = self.adapter.get_all_ocr_engines()
        results = []

        for eng in engines:
            logger.info(f"Diag: 正在测试 OCR 引擎: {eng.name}")
            try:
                times = []
                # 跑3次取平均
                for i in range(3):
                    start = time.perf_counter()
                    text = eng.recognize(detail_img) # 触发平台 OCR 的内部日志
                    # 在日志里打印识别出的前几个字，这样 text 就被“使用”了
                    preview = text.replace('\n', ' ')[:15]

                    times.append((time.perf_counter() - start) * 1000)
                    logger.debug(f"Diag: {eng.name} 第 {i+1} 次尝试耗时: {times[-1]:.2f}ms | 预览: [{preview}...]")
                
                avg_ms = np.mean(times)
                results.append({"name": eng.name, "avg_ms": avg_ms})
                logger.success(f"Diag: {eng.name} 测试完成，平均耗时: {avg_ms:.2f}ms")
            except Exception as e:
                logger.error(f"Diag: 引擎 {eng.name} 运行崩溃: {e}")

        if not results:
            return None
            
        best = min(results, key=lambda x: x['avg_ms'])
        return {"best_engine_name": best['name'], "all": results}