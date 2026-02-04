# core/diagnostics.py
import time
import os
import cv2
import onnxruntime as ort
import numpy as np
from loguru import logger

import config
from core.detectors.yolo_detector import YoloDetector
from core.comparators.feature_matcher import FeatureMatcher
from platforms.adapter import PlatformAdapter

class SystemDiagnostics:
    def __init__(self):
        logger.debug("Diag: 正在初始化诊断引擎...")
        self.adapter = PlatformAdapter()

    def check_environment(self):
        """[基础检查] 检查核心模型与数据库文件是否存在"""
        model_ok = os.path.exists(config.MODEL_PATH)
        db_ok = os.path.exists(config.ITEMS_DB_PATH)
        return {
            "status": model_ok and db_ok,
            "details": f"模型文件:{'OK' if model_ok else '缺失'}, 数据库:{'OK' if db_ok else '缺失'}"
        }

    def benchmark_yolo(self, image_path):
        """[任务 1] YOLO 性能测试：评估各后端并计算建议刷新率"""
        logger.info(f"Diag: 开始 YOLO 性能压测，图片路径: {image_path}")
        img = cv2.imread(image_path)
        if img is None: 
            logger.error("Diag: YOLO 测试图片读取失败")
            return None
        
        providers = ort.get_available_providers()
        results = []

        for p in providers:
            logger.info(f"Diag: 正在测试 Provider: {p}")
            try:
                # 实例化 YoloDetector 触发内部详尽日志
                detector = YoloDetector(config.MODEL_PATH, providers=[p])
                
                # 预热一次
                detector.detect_stream(img)
                
                # 正式侧速
                times = []
                for _ in range(15):
                    start = time.perf_counter()
                    detector.detect_stream(img) # 触发每一帧的耗时拆解日志
                    times.append((time.perf_counter() - start) * 1000)
                
                avg_ms = np.mean(times)
                results.append({"provider": p, "avg_ms": avg_ms})
                logger.success(f"Diag: {p} 平均耗时: {avg_ms:.2f}ms")
            except Exception as e:
                logger.warning(f"Diag: Provider {p} 无法运行: {e}")
                continue

        if not results: 
            return None
        
        best = min(results, key=lambda x: x['avg_ms'])
        # 建议 FPS = 1000 / (耗时 * 1.5倍安全冗余)
        suggested_fps = int(1000 / (best['avg_ms'] * 1.5))
        return {
            "best_provider": best['provider'], 
            "avg_ms": best['avg_ms'], 
            "suggested_fps": min(suggested_fps, 30),
            "all": results
        }

    def benchmark_matcher(self, image_samples: dict):
        """[任务 2] ORB 匹配可用性测试：分尺寸反馈耗时与结果"""
        logger.info("Diag: 开始 ORB 匹配可用性测试...")
        # 实例化 FeatureMatcher 触发特征库加载日志
        matcher = FeatureMatcher()
        report = {}
        
        for size, img in image_samples.items():
            if img is None:
                logger.warning(f"Diag: {size} 尺寸测试图为空，已跳过")
                continue
            
            logger.info(f"Diag: 正在比对 [{size}] 分类样本...")
            start = time.perf_counter()
            # 这里的 match 方法会触发详尽的暴力比对过程日志
            res = matcher.match(img, size) 
            dur = (time.perf_counter() - start) * 1000
            
            if res:
                match_id, score = res[0]
                logger.success(f"Diag: [{size}] 匹配成功! 得分: {score:.4f}")
                report[size] = {"time_ms": dur, "matched": match_id, "score": score}
            else:
                logger.error(f"Diag: [{size}] 匹配失败 (低于阈值)")
                report[size] = {"time_ms": dur, "matched": None, "score": 0.0}
        return report

    def benchmark_ocr(self, detail_img):
        """[任务 3] OCR 性能测试：横评所有引擎并自动选优"""
        logger.info("Diag: 开始 OCR 引擎全量性能横评...")
        engines = self.adapter.get_all_ocr_engines()
        results = []

        for eng in engines:
            logger.info(f"Diag: 正在测试引擎: {eng.name}")
            try:
                times = []
                for i in range(3):
                    start = time.perf_counter()
                    _text = eng.recognize(detail_img) # 触发平台原生的细节日志
                    times.append((time.perf_counter() - start) * 1000)
                
                avg_ms = np.mean(times)
                results.append({"name": eng.name, "avg_ms": avg_ms})
                logger.success(f"Diag: {eng.name} 平均耗时: {avg_ms:.2f}ms")
            except Exception as e:
                logger.error(f"Diag: OCR 引擎 {eng.name} 运行异常: {e}")

        if not results: 
            return None
        
        best = min(results, key=lambda x: x['avg_ms'])
        return {"best_engine_name": best['name'], "all": results}