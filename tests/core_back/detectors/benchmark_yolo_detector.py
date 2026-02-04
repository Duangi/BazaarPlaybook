import time
import cv2
import numpy as np
from loguru import logger

from core.detectors.yolo_detector import YoloDetector
import onnxruntime

def run_benchmark():
    """
    遍历所有可用的 ONNX Execution Providers，并测试其推理性能。
    """
    logger.info("========== 开始 ONNX Provider 性能基准测试 ==========")

    model_path = "assets/models/best.onnx"
    image_path = "tests/assets/yolo_test.png"
    
    # 准备测试图片
    image = cv2.imread(image_path)
    if image is None:
        logger.error(f"测试图片加载失败: {image_path}")
        return

    # 获取所有可用的 providers
    available_providers = onnxruntime.get_available_providers()
    logger.info(f"系统上检测到以下可用 Providers: {available_providers}")

    results = {}

    # 遍历每一个 provider
    for provider in available_providers:
        logger.info(f"--- 正在测试 Provider: {provider} ---")
        try:
            # 为每个 provider 创建一个新的 detector 实例
            # 注意：我们传入 providers=[provider] 来强制使用它
            detector = YoloDetector(model_path, providers=[provider])
            
            # 预热运行 (Warm-up)
            # 第一次推理通常会包含一些初始化开销，不应计入总时间
            logger.debug("进行预热推理...")
            detector.detect(image)

            # 多次运行以获得稳定结果
            num_runs = 30
            timings = []
            logger.debug(f"开始 {num_runs} 次计时推理...")
            for _ in range(num_runs):
                start_time = time.perf_counter()
                detector.detect(image)
                end_time = time.perf_counter()
                timings.append((end_time - start_time) * 1000) # 转换为毫秒

            # 计算统计数据
            avg_time = np.mean(timings)
            min_time = np.min(timings)
            max_time = np.max(timings)
            
            results[provider] = avg_time
            logger.success(
                f"测试完成: "
                f"平均耗时={avg_time:.2f} ms, "
                f"最快={min_time:.2f} ms, "
                f"最慢={max_time:.2f} ms"
            )

        except Exception as e:
            results[provider] = -1.0 # -1.0 表示失败
            logger.error(f"Provider '{provider}' 初始化或推理失败: {e}")

    logger.info("========== 性能基准测试结束 ==========")
    logger.info("测试结果摘要 (平均耗时 ms):")
    # 排序并打印最终结果
    sorted_results = sorted(results.items(), key=lambda item: item[1] if item[1] > 0 else float('inf'))
    for provider, avg_time in sorted_results:
        status = f"{avg_time:.2f} ms" if avg_time > 0 else "失败"
        logger.info(f"- {provider:<25}: {status}")

if __name__ == "__main__":
    run_benchmark()