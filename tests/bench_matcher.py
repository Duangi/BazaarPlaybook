import cv2
import json
from loguru import logger
from core.diagnostics import SystemDiagnostics
from utils.logger import setup_logger
import config

def main():
    # 1. 强制初始化日志为 DEBUG 模式，这样你就能看到上面的 noisy 输出
    setup_logger(is_gui_app=False)
    logger.info("=== 启动 ORB 匹配深度自检程序 ===")

    # 2. 准备 ID -> Name 的转换字典
    try:
        with open(config.ITEMS_DB_PATH, 'r', encoding='utf-8') as f:
            db = json.load(f)
            id_to_name = {item['id']: item['name_cn'] for item in db}
    except Exception as e:
        logger.error(f"数据库加载失败: {e}")
        return

    # 3. 模拟三张图 (确保你的 assets 文件夹里有这些图)
    samples = {
        "Small": cv2.imread("tests/assets/small.png"),   # 预期结果: 方便面
        "Medium": cv2.imread("tests/assets/medium.png"), # 预期结果: 搅拌机
        "Large": cv2.imread("tests/assets/large.png")    # 预期结果: 冷库
    }

    diag = SystemDiagnostics()
    report = diag.benchmark_matcher(samples)

    print("\n" + "="*60)
    print(f"{'分类':<8} | {'耗时(ms)':<10} | {'匹配结果':<12} | {'匹配得分'}")
    print("-" * 60)
    
    for size, data in report.items():
        m_id = data['matched']
        name = id_to_name.get(m_id, "Unknown") if m_id else "None"
        score = data.get('score', 0.0)
        
        # 打印最终结果表格
        print(f"{size:<10} | {data['time_ms']:10.2f} | {name:<12} | {score:.4f}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()