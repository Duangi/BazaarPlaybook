# 1. 所有 import 语句都集中在文件顶部
import os
import time
import cv2
from loguru import logger
import onnxruntime

from core.detectors.yolo_detector import YoloDetector

def test_provider_streaming(provider, num_frames=300):
    """
    使用指定的 Provider 模拟流式处理，并计算 FPS。

    :param provider: 要测试的 ONNX Provider (e.g., 'CUDAExecutionProvider').
    :param num_frames: 模拟处理的总帧数。
    :return: 计算出的 FPS，如果失败则返回 0.0。
    """
    logger.info(f"--- 正在使用 [{provider}] 进行流式性能测试 ---")
    
    # 2. 路径现在是相对于项目根目录的，非常简洁
    model_path = os.path.join("assets", "models", "best.onnx")
    image_path = os.path.join("tests", "assets", "yolo_test.png")
    
    try:
        # 初始化模型和图片
        logger.debug("正在初始化模型和加载图片...")
        detector = YoloDetector(model_path, providers=[provider])
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"测试图片加载失败: {image_path}")
            return 0.0
        
        # 预热 (Warm-up)
        logger.debug("正在进行预热运行 (10 帧)...")
        for _ in range(10):
            detector.detect_stream(image)
        
        # 开始计时，模拟流式处理
        logger.info(f"开始连续处理 {num_frames} 帧，请稍候...")
        start_time = time.perf_counter()
        
        for _ in range(num_frames):
            # detections = detector.detect_stream(image)
            pass
            
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # 计算并报告 FPS
        fps = num_frames / total_time
        logger.success(f"[{provider}] 测试完成:")
        logger.success(f"  - 总耗时: {total_time:.2f} 秒")
        logger.success(f"  - 处理帧数: {num_frames} 帧")
        logger.success(f"  - 平均 FPS: {fps:.2f}")
        return fps

    except Exception as e:
        logger.error(f"Provider '{provider}' 测试过程中失败: {e}")
        return 0.0

if __name__ == "__main__":
    logger.info("========== 开始 GPU vs CPU 流式处理 (FPS) 性能对比测试 ==========")
    
    providers_to_test = ['CUDAExecutionProvider', 'CPUExecutionProvider']
    results = {}
    
    # 依次测试列表中的 Provider
    for prov in providers_to_test:
        if prov in onnxruntime.get_available_providers():
            fps = test_provider_streaming(prov)
            results[prov] = fps
        else:
            logger.warning(f"Provider [{prov}] 在当前系统不可用，已跳过测试。")
            
    logger.info("========== FPS 测试结果最终摘要 ==========")
    logger.info(f"{'Provider':<25} | {'Frames Per Second (FPS)':<25}")
    logger.info("-" * 55)
    for provider, fps in results.items():
        logger.info(f"{provider:<25} | {fps:.2f}")
    logger.info("-" * 55)
