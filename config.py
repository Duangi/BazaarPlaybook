# config.py
import os

CLS_MAP = {
    'DAY': 0, 'DETAIL': 1, 'EVENT': 2, 'ITEM': 3,
    'MONSTER_ICON': 4, 'NEXT': 5, 'RANDOM_ICON': 6,
    'SHOP_ICON': 7, 'SKILL': 8, 'STORE': 9
}

# 路径配置
MODEL_PATH = "assets/models/yolo11n/best.onnx"
ITEMS_DB_PATH = "assets/json/items_db.json"
CARD_IMAGES_DIR = "assets/images/card"
MONSTER_CHAR_DIR = "assets/images/monster_char"
CACHE_DIR = "assets/features_cache"
STATIC_LIB_FILE = os.path.join(CACHE_DIR, "ratio_based_library.pkl")
MONSTER_LIB_FILE = os.path.join(CACHE_DIR, "monster_library.pkl")
USER_MEMORY_FILE = os.path.join(CACHE_DIR, "user_memory_library.pkl")

# 算法参数对齐 Rust
ORB_RATIO = 0.75
ORB_MATCH_THRESHOLD = 0.05 # 匹配门槛


# OCR 配置
OCR_CONFIDENCE_THRESHOLD = 0.8  # OCR 结果置信度
FUZZY_MATCH_THRESHOLD = 60      # 模糊匹配门槛 (0-100)

# 详情框内部裁剪比例 (根据你之前发的那张棕色框截图)
# 名字通常在详情框顶部的 15% 区域
DETAIL_NAME_AREA = {
    'top': 0.02,    # 稍微留一点边
    'bottom': 0.18, # 截取到框高度的 18%
    'left': 0.05,
    'right': 0.80   # 避开右侧的图标
}