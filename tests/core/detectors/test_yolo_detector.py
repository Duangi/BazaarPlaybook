import os
import cv2
from loguru import logger

from core.detectors.yolo_detector import YoloDetector

def run_yolo_test():
    """
    执行一次完整的 YOLO ONNX 推理测试流程。
    """
    logger.info("========== 开始 YOLO ONNX 推理全流程测试 ==========")

    # 定义资源路径 (使用 os.path.join 保证跨平台兼容性)
    model_path = "assets/models/best.onnx"
    test_image_path = "tests/assets/yolo_test.png"
    # 1. 检查文件是否存在
    logger.info("步骤 1/4: 检查资源文件")
    if not os.path.exists(model_path):
        logger.error(f"模型文件不存在: {model_path}")
        return
    if not os.path.exists(test_image_path):
        logger.error(f"测试图片不存在: {test_image_path}")
        return
    logger.success("资源文件检查通过。")

    # 2. 加载图片
    logger.info("步骤 2/4: 加载测试图片")
    image = cv2.imread(test_image_path)
    if image is None:
        logger.error(f"使用 OpenCV 加载图片失败: {test_image_path}")
        return
    logger.success(f"图片加载成功，尺寸: {image.shape[1]}x{image.shape[0]}")

    # 3. 初始化识别器 (这将触发模型加载)
    logger.info("步骤 3/4: 初始化 YOLO 识别器")
    try:
        detector = YoloDetector(model_path=model_path, use_gpu=True)
    except Exception:
        logger.error("识别器初始化失败，请检查模型文件或依赖项。")
        return
    logger.success("识别器初始化成功。")

    # 4. 执行检测
    logger.info("步骤 4/4: 执行目标检测")
    detections = detector.detect(image)

    # 结果展示
    if detections:
        logger.info("========== 测试报告：检测成功 ==========")
        logger.info(f"成功检测到 {len(detections)} 个目标:")
        for i, det in enumerate(detections):
            logger.info(
                f"  目标 {i+1}: "
                f"类别ID={det['class_id']}, "
                f"置信度={det['confidence']:.2f}, "
                f"边界框 (x,y,w,h)={det['box']}"
            )
        # (可选) 在图片上绘制结果并显示
        result_image_path = "tests/assets/yolo_test_result.png"
        for det in detections:
            box = det['box']
            x, y, w, h = box
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.imwrite(result_image_path, image)
        logger.info(f"检测结果已绘制并保存到 {result_image_path}")

    else:
        logger.warning("========== 测试报告：未检测到任何目标 ==========")
        logger.warning("这可能是正常的 (图片中无目标)，也可能表示模型阈值设置过高或模型性能问题。")

    logger.info("========== YOLO ONNX 推理全流程测试结束 ==========")

if __name__ == "__main__":
    run_yolo_test()



