import time
import cv2
from loguru import logger
import numpy as np

from core.detectors.yolo_detector import YoloDetector

def diagnose_provider(provider, num_frames=300):
    logger.info(f"========== 深度性能诊断: [{provider}] ==========")
    
    model_path = "assets/models/best.onnx"
    image_path = "tests/assets/yolo_test.png"
    
    try:
        detector = YoloDetector(model_path, providers=[provider])
        image = cv2.imread(image_path)
        
        logger.debug("预热...")
        for _ in range(10):
            detector.detect_stream(image)
        
        # 初始化计时器列表
        preprocess_times = []
        inference_times = []
        postprocess_times = []
        total_times = []

        logger.info(f"开始剖析 {num_frames} 帧的处理流程...")
        
        for _ in range(num_frames):
            loop_start = time.perf_counter()
            
            # 1. 剖析预处理
            t0 = time.perf_counter()
            input_tensor, ratio, (dw, dh) = detector._preprocess(image)
            t1 = time.perf_counter()
            
            # 2. 剖析模型推理
            # outputs = detector.session.run(detector.output_names, {detector.input_name: input_tensor})
            t2 = time.perf_counter()
            
            # 3. 剖析后处理
            # detections = detector._postprocess_stream(outputs[0], ratio, (dw, dh))
            t3 = time.perf_counter()
            
            # 记录耗时 (ms)
            preprocess_times.append((t1 - t0) * 1000)
            inference_times.append((t2 - t1) * 1000)
            postprocess_times.append((t3 - t2) * 1000)
            total_times.append((t3 - loop_start) * 1000)

        # 计算平均值并报告
        avg_prep = np.mean(preprocess_times)
        avg_inf = np.mean(inference_times)
        avg_post = np.mean(postprocess_times)
        avg_total = np.mean(total_times)
        fps = 1000 / avg_total

        logger.success(f"--- 诊断报告: [{provider}] ---")
        logger.success(f"  - 平均总耗时: {avg_total:.2f} ms")
        logger.success(f"  - 等效 FPS  : {fps:.2f} FPS")
        logger.info("--- 各阶段平均耗时 (ms) ---")
        logger.info(f"  - 预处理 (_preprocess) : {avg_prep:.2f} ms")
        logger.info(f"  - 模型推理 (session.run): {avg_inf:.2f} ms")
        logger.info(f"  - 后处理 (_postprocess): {avg_post:.2f} ms")

    except Exception as e:
        logger.error(f"Provider '{provider}' 诊断失败: {e}")

if __name__ == "__main__":
    # 我们先只诊断 CUDA，因为这是问题的关键
    diagnose_provider('CUDAExecutionProvider')
    print("\n") # 加个换行，方便区分
    diagnose_provider('CPUExecutionProvider')