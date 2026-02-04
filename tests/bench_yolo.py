from loguru import logger
from core.diagnostics import SystemDiagnostics
from utils.logger import setup_logger
from data_manager.config_manager import ConfigManager

def main():
    # ✅ 关键：设置为非 GUI 模式，开启详尽输出
    setup_logger(is_gui_app=False)
    
    logger.info("=== 启动 YOLO 性能深度基准测试 ===")
    
    img_path = "tests/assets/yolo_test.png"
    diag = SystemDiagnostics()
    
    # 核心逻辑会触发 YoloDetector 内部的所有详尽 logger
    res = diag.benchmark_yolo(img_path)
    
    if res:
        # 保存结果
        ConfigManager().save({
            "preferred_provider": res['best_provider'],
            "yolo_fps": res['suggested_fps']
        })
        logger.success(f"测试结束。建议 Provider: {res['best_provider']}, 建议 FPS: {res['suggested_fps']}")

if __name__ == "__main__":
    main()