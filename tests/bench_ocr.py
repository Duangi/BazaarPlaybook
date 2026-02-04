# tests/bench_ocr.py
import cv2
import os
from loguru import logger

from core.diagnostics import SystemDiagnostics
from utils.logger import setup_logger

def main():
    setup_logger(is_gui_app=False)
    
    # ❌ 报错点就在这：请仔细检查文件名和路径是否完全正确
    img_path = "tests/assets/detail/detail_1.png" 
    
    if not os.path.exists(img_path):
        logger.error(f"找不到测试图片: {os.path.abspath(img_path)}")
        return

    img = cv2.imread(img_path)
    if img is None:
        logger.error("图片文件损坏或无法被 OpenCV 解码")
        return

    diag = SystemDiagnostics()
    res = diag.benchmark_ocr(img)
    
    if res:
        logger.success(f"诊断结论：最优 OCR 引擎为 {res['best_engine_name']}")

if __name__ == "__main__":
    main()