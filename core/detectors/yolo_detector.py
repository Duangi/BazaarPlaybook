import sys
import cv2
import time
import numpy as np
import onnxruntime
from loguru import logger

class YoloDetector:
    def __init__(self, model_path, use_gpu=True, confidence_thresh=0.5, nms_thresh=0.4, providers=None):
        """
        初始化 YOLOv8 ONNX 识别器（深度日志诊断版）。
        """
        self.model_path = model_path
        self.use_gpu = use_gpu
        self.confidence_thresh = confidence_thresh
        self.nms_thresh = nms_thresh
        self.session = None
        self.input_name = None
        self.output_names = None
        self.input_shape = (640, 640)
        self.actual_provider = None

        self._initialize_model(providers)

    def _get_onnx_providers(self):
        """
        智能获取可用的 ONNX Execution Providers。
        """
        providers = []
        available_providers = onnxruntime.get_available_providers()
        logger.debug(f"YOLO: 系统支持的 Providers 列表: {available_providers}")

        if not self.use_gpu:
            logger.info("YOLO: 用户已禁用 GPU，将强制使用 CPU 进行推理。")
            providers.append('CPUExecutionProvider')
            return providers

        logger.info("YOLO: 硬件加速已启用，正在筛选最优后端...")
        
        if sys.platform == "win32":
            if 'CUDAExecutionProvider' in available_providers:
                logger.success("YOLO: 检测到 NVIDIA GPU (CUDA)，性能最优方案。")
                providers.append('CUDAExecutionProvider')
            elif 'DmlExecutionProvider' in available_providers:
                logger.success("YOLO: 检测到 DirectML 支持 (AMD/Intel/NVIDIA)，兼容性加速方案。")
                providers.append('DmlExecutionProvider')
        
        elif sys.platform == "darwin":
            if 'CoreMLExecutionProvider' in available_providers:
                logger.success("YOLO: 检测到 Apple Silicon (CoreML) 加速支持。")
                providers.append('CoreMLExecutionProvider')

        providers.append('CPUExecutionProvider')

        if len(providers) == 1:
            logger.warning("YOLO: 虽然启用了 GPU，但未找到匹配的硬件驱动，将回退到 CPU。")
        else:
            logger.info(f"YOLO: 尝试加载顺序: {providers}")
            
        return providers

    def _initialize_model(self, providers=None):
        """加载 ONNX 模型并初始化会话，带耗时统计。"""
        load_start = time.perf_counter()
        logger.info(f"YOLO: 正在从磁盘加载模型: {self.model_path}")

        if providers is None:
            providers = self._get_onnx_providers()

        try:
            self.session = onnxruntime.InferenceSession(self.model_path, providers=providers)
            
            # 确定最终被选中的后端
            self.actual_provider = self.session.get_providers()[0]
            load_cost = (time.perf_counter() - load_start) * 1000
            
            logger.success(f"YOLO: 模型加载成功 | 实际后端: {self.actual_provider} | 耗时: {load_cost:.2f}ms")

            if 'CPU' in self.actual_provider and self.use_gpu and len(providers) > 1:
                 logger.warning("YOLO: GPU 初始化失败，ONNX 已被迫回退到 CPU 模式，请检查驱动环境。")

            model_inputs = self.session.get_inputs()
            self.input_name = model_inputs[0].name
            self.input_shape = model_inputs[0].shape[2:]

            model_outputs = self.session.get_outputs()
            self.output_names = [output.name for output in model_outputs]
            
            logger.debug(f"YOLO: 输入节点: {self.input_name} {self.input_shape}")
            logger.debug(f"YOLO: 输出节点: {self.output_names}")

        except Exception as e:
            logger.error(f"YOLO: 关键错误 - 模型初始化失败: {e}")
            raise

    def detect(self, image: np.ndarray):
        """对单张图片进行完整的目标检测流程（带详细全步耗时分析）。"""
        t_all_start = time.perf_counter()
        
        # 1. 预处理
        t0 = time.perf_counter()
        input_tensor, ratio, (dw, dh) = self._preprocess(image)
        t_pre = (time.perf_counter() - t0) * 1000

        # 2. 推理
        try:
            t1 = time.perf_counter()
            outputs = self.session.run(self.output_names, {self.input_name: input_tensor})
            t_inf = (time.perf_counter() - t1) * 1000
        except Exception as e:
            logger.error(f"YOLO: 推理阶段崩溃: {e}")
            return []

        # 3. 后处理
        t2 = time.perf_counter()
        detections = self._postprocess(outputs[0], ratio, (dw, dh))
        t_post = (time.perf_counter() - t2) * 1000
        
        t_all_cost = (time.perf_counter() - t_all_start) * 1000
        
        # 详尽的诊断日志
        logger.debug(f"YOLO 性能剖析: 总计 {t_all_cost:.1f}ms | 预处理 {t_pre:.1f}ms | 推理 {t_inf:.1f}ms | 后处理 {t_post:.1f}ms")
        logger.info(f"YOLO 结果: 成功识别到 {len(detections)} 个目标")
        
        return detections

    def detect_stream(self, image: np.ndarray):
        """
        高性能流式处理，仅保留核心耗时分析日志（DEBUG级别）。
        """
        t_start = time.perf_counter()
        
        input_tensor, ratio, (dw, dh) = self._preprocess(image)
        try:
            outputs = self.session.run(self.output_names, {self.input_name: input_tensor})
        except Exception:
            return []

        detections = self._postprocess_stream(outputs[0], ratio, (dw, dh))
        
        t_cost = (time.perf_counter() - t_start) * 1000
        # 流式检测只在 DEBUG 级别输出，不干扰主控制台
        logger.debug(f"YOLO Stream: 推理完成，耗时 {t_cost:.2f}ms, 发现 {len(detections)} 个目标")
        
        return detections

    def _preprocess(self, image: np.ndarray):
        """图像预处理逻辑。"""
        img_h, img_w = image.shape[:2]
        input_h, input_w = self.input_shape

        ratio = min(input_w / img_w, input_h / img_h)
        new_w, new_h = int(img_w * ratio), int(img_h * ratio)
        dw, dh = (input_w - new_w) / 2, (input_h - new_h) / 2

        resized_img = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        padded_img = cv2.copyMakeBorder(resized_img, int(dh), int(dh) + (input_h - new_h) % 2,
                                        int(dw), int(dw) + (input_w - new_w) % 2,
                                        cv2.BORDER_CONSTANT, value=(114, 114, 114))

        blob = cv2.dnn.blobFromImage(padded_img, 1 / 255.0, (input_w, input_h), swapRB=True, crop=False)
        return blob, ratio, (dw, dh)

    def _postprocess(self, output, ratio, pad):
        """带 NMS 细节统计的后处理。"""
        output = output[0].T
        boxes, scores, class_ids = [], [], []

        for row in output:
            confidence = row[4:].max()
            if confidence >= self.confidence_thresh:
                class_id = int(row[4:].argmax())
                scores.append(float(confidence))
                class_ids.append(class_id)
                
                cx, cy, w, h = row[:4]
                x1 = int((cx - w / 2 - pad[0]) / ratio)
                y1 = int((cy - h / 2 - pad[1]) / ratio)
                boxes.append([x1, y1, int(w / ratio), int(h / ratio)])

        logger.debug(f"YOLO NMS: 原始候选框数 {len(boxes)}")
        indices = cv2.dnn.NMSBoxes(boxes, scores, self.confidence_thresh, self.nms_thresh)
        
        detections = []
        if len(indices) > 0:
            for i in indices.flatten():
                detections.append({
                    'class_id': class_ids[i],
                    'confidence': scores[i],
                    'box': boxes[i]
                })
        return detections

    def _postprocess_stream(self, output, ratio, pad):
        """流式后处理，保持极简输出。"""
        output = output[0].T
        boxes, scores, class_ids = [], [], []

        for row in output:
            confidence = row[4:].max()
            if confidence >= self.confidence_thresh:
                cx, cy, w, h = row[:4]
                x1 = int((cx - w / 2 - pad[0]) / ratio)
                y1 = int((cy - h / 2 - pad[1]) / ratio)
                boxes.append([x1, y1, int(w / ratio), int(h / ratio)])
                scores.append(float(confidence))
                class_ids.append(int(row[4:].argmax()))

        indices = cv2.dnn.NMSBoxes(boxes, scores, self.confidence_thresh, self.nms_thresh)
        
        detections = []
        if len(indices) > 0:
            for i in indices.flatten():
                detections.append({
                    'class_id': class_ids[i],
                    'confidence': scores[i],
                    'box': boxes[i]
                })
        return detections