import sys
import cv2
import numpy as np
import onnxruntime
from loguru import logger

class YoloDetector:
    def __init__(self, model_path, use_gpu=True, confidence_thresh=0.5, nms_thresh=0.4, providers=None):
        """
        初始化 YOLOv8 ONNX 识别器。

        :param model_path: ONNX 模型文件的路径。
        :param use_gpu: 是否尝试使用 GPU。如果为 False，将强制使用 CPU。
        :param confidence_thresh: 置信度阈值。
        :param nms_thresh: 非极大值抑制阈值。
        """
        self.model_path = model_path
        self.use_gpu = use_gpu
        self.confidence_thresh = confidence_thresh
        self.nms_thresh = nms_thresh
        self.session = None
        self.input_name = None
        self.output_names = None
        self.input_shape = (640, 640)

        self._initialize_model(providers)

    def _get_onnx_providers(self):
        """
        智能获取可用的 ONNX Execution Providers.
        根据用户设置、操作系统和硬件，返回一个有序的 Provider 列表。
        ONNX Runtime 会依次尝试列表中的 Provider，直到成功为止。
        """
        providers = []
        available_providers = onnxruntime.get_available_providers()
        logger.debug(f"系统上可用的 ONNX Providers: {available_providers}")

        if not self.use_gpu:
            logger.info("用户已禁用 GPU，强制使用 CPU。")
            providers.append('CPUExecutionProvider')
            return providers

        logger.info("GPU 已启用，开始检测可用硬件...")
        
        # 平台特定逻辑
        if sys.platform == "win32":
            # Windows: 优先 CUDA, 其次 DirectML
            if 'CUDAExecutionProvider' in available_providers:
                logger.success("检测到 NVIDIA GPU (CUDA)，将优先使用。")
                providers.append('CUDAExecutionProvider')
            elif 'DmlExecutionProvider' in available_providers:
                logger.success("检测到 DirectML-capable GPU (AMD/Intel/NVIDIA)，将使用 DirectML。")
                providers.append('DmlExecutionProvider')
        
        elif sys.platform == "darwin":
            # macOS: 只有 CoreML
            if 'CoreMLExecutionProvider' in available_providers:
                logger.success("检测到 Apple Silicon/AMD GPU (CoreML)，将优先使用。")
                providers.append('CoreMLExecutionProvider')

        # 添加 CPU 作为最终的回退选项
        providers.append('CPUExecutionProvider')

        if len(providers) == 1:
            logger.warning("用户请求使用 GPU，但未找到任何受支持的 GPU Provider。将回退到 CPU。")
        else:
            logger.info(f"将按此顺序尝试使用 Providers: {providers}")
            
        return providers

    def _initialize_model(self, providers=None):
        """加载 ONNX 模型并初始化会话。"""
        logger.info(f"开始加载 ONNX 模型，路径: {self.model_path}")

        if providers is None:
            providers = self._get_onnx_providers()
        else:
            logger.info(f"使用用户指定的 ONNX Providers: {providers}")

        try:
            self.session = onnxruntime.InferenceSession(self.model_path, providers=providers)
            
            # 检查实际使用的 Provider
            actual_provider = self.session.get_providers()[0]
            logger.success(f"ONNX 模型加载成功，实际使用的 Provider: {actual_provider}")
            if 'CPU' in actual_provider and self.use_gpu and len(providers) > 1:
                 logger.warning("GPU 初始化可能失败，ONNX 已自动回退到 CPU。")


            model_inputs = self.session.get_inputs()
            self.input_name = model_inputs[0].name
            self.input_shape = model_inputs[0].shape[2:]

            model_outputs = self.session.get_outputs()
            self.output_names = [output.name for output in model_outputs]
            
            logger.debug(f"模型输入名: {self.input_name}, 输入形状: {self.input_shape}")
            logger.debug(f"模型输出名: {self.output_names}")

        except FileNotFoundError:
            logger.error(f"模型文件未找到: {self.model_path}")
            raise
        except Exception as e:
            logger.error(f"加载 ONNX 模型失败: {e}")
            logger.error("这可能是由于 ONNX Runtime 与 CUDA/DirectML 版本不兼容导致的。")
            logger.error("请确保您的显卡驱动和依赖库已正确安装。")
            raise

    # ... detect, _preprocess, _postprocess 方法保持不变 ...
    def detect(self, image: np.ndarray):
        """对单张图片进行目标检测。"""
        logger.info("开始进行目标检测流程...")
        
        # 1. 预处理
        input_tensor, ratio, (dw, dh) = self._preprocess(image)
        logger.debug(f"图片预处理完成。缩放比例: {ratio}, 填充: ({dw}, {dh})")

        # 2. 推理
        try:
            logger.debug("正在执行模型推理...")
            outputs = self.session.run(self.output_names, {self.input_name: input_tensor})
            logger.success("模型推理完成。")
            logger.debug(f"模型原始输出 shape: {outputs[0].shape}")
        except Exception as e:
            logger.error(f"模型推理过程中发生错误: {e}")
            return []

        # 3. 后处理
        detections = self._postprocess(outputs[0], ratio, (dw, dh))
        logger.info(f"检测到 {len(detections)} 个目标。")
        
        return detections

    def detect_stream(self, image: np.ndarray):
        """
        对单张图片进行目标检测，无日志记录，专为高性能流式处理设计。
        """
        # 1. 预处理
        input_tensor, ratio, (dw, dh) = self._preprocess(image)

        # 2. 推理
        try:
            outputs = self.session.run(self.output_names, {self.input_name: input_tensor})
        except Exception:
            # 在流式处理中，如果一帧失败，我们通常返回空结果并继续
            return []

        # 3. 后处理
        detections = self._postprocess_stream(outputs[0], ratio, (dw, dh))
        
        return detections

    def _preprocess(self, image: np.ndarray):
        """将原始图片预处理为模型输入格式。"""
        img_h, img_w = image.shape[:2]
        input_h, input_w = self.input_shape

        # 计算缩放比例和填充大小
        ratio = min(input_w / img_w, input_h / img_h)
        new_w, new_h = int(img_w * ratio), int(img_h * ratio)
        dw, dh = (input_w - new_w) / 2, (input_h - new_h) / 2

        # 缩放和填充
        resized_img = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        padded_img = cv2.copyMakeBorder(resized_img, int(dh), int(dh) + (input_h - new_h) % 2,
                                        int(dw), int(dw) + (input_w - new_w) % 2,
                                        cv2.BORDER_CONSTANT, value=(114, 114, 114))

        # 转换: BGR -> RGB, HWC -> CHW, 归一化
        blob = cv2.dnn.blobFromImage(padded_img, 1 / 255.0, (input_w, input_h), swapRB=True, crop=False)
        return blob, ratio, (dw, dh)

    def _postprocess(self, output, ratio, pad):
        """处理模型输出，进行NMS并还原坐标。"""
        logger.debug("开始后处理模型输出...")
        
        # YOLOv8 的输出格式是 [batch, 4 + num_classes, num_boxes]
        # 我们需要将其转置为 [batch, num_boxes, 4 + num_classes]
        output = output[0].T
        
        boxes = []
        scores = []
        class_ids = []

        for row in output:
            # 前4个是坐标 (cx, cy, w, h)，后面是类别分数
            confidence = row[4:].max()
            if confidence >= self.confidence_thresh:
                class_id = row[4:].argmax()
                scores.append(confidence)
                class_ids.append(class_id)
                
                # 转换坐标
                cx, cy, w, h = row[:4]
                x1 = int((cx - w / 2 - pad[0]) / ratio)
                y1 = int((cy - h / 2 - pad[1]) / ratio)
                x2 = int((cx + w / 2 - pad[0]) / ratio)
                y2 = int((cy + h / 2 - pad[1]) / ratio)
                boxes.append([x1, y1, x2 - x1, y2 - y1]) # xywh 格式

        # 应用非极大值抑制 (NMS)
        indices = cv2.dnn.NMSBoxes(boxes, scores, self.confidence_thresh, self.nms_thresh)
        
        detections = []
        if len(indices) > 0:
            for i in indices.flatten():
                detections.append({
                    'class_id': class_ids[i],
                    'confidence': scores[i],
                    'box': boxes[i] # [x, y, w, h]
                })
        logger.debug(f"NMS 处理后剩余 {len(detections)} 个目标。")
        return detections

    # 在流式处理模式下，输出格式与 detect 方法相同，但不记录日志
    def _postprocess_stream(self, output, ratio, pad):
        # YOLOv8 的输出格式是 [batch, 4 + num_classes, num_boxes]
        # 我们需要将其转置为 [batch, num_boxes, 4 + num_classes]
        output = output[0].T
        
        boxes = []
        scores = []
        class_ids = []

        for row in output:
            # 前4个是坐标 (cx, cy, w, h)，后面是类别分数
            confidence = row[4:].max()
            if confidence >= self.confidence_thresh:
                class_id = row[4:].argmax()
                scores.append(confidence)
                class_ids.append(class_id)
                
                # 转换坐标
                cx, cy, w, h = row[:4]
                x1 = int((cx - w / 2 - pad[0]) / ratio)
                y1 = int((cy - h / 2 - pad[1]) / ratio)
                x2 = int((cx + w / 2 - pad[0]) / ratio)
                y2 = int((cy + h / 2 - pad[1]) / ratio)
                boxes.append([x1, y1, x2 - x1, y2 - y1]) # xywh 格式

        # 应用非极大值抑制 (NMS)
        indices = cv2.dnn.NMSBoxes(boxes, scores, self.confidence_thresh, self.nms_thresh)
        
        detections = []
        if len(indices) > 0:
            for i in indices.flatten():
                detections.append({
                    'class_id': class_ids[i],
                    'confidence': scores[i],
                    'box': boxes[i] # [x, y, w, h]
                })
        return detections