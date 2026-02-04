import os
import cv2
import pickle
import json
import numpy as np
from loguru import logger
import config

class FeatureMatcher:
    def __init__(self):
        # 对齐 Rust 版 nfeatures=500
        self.orb = cv2.ORB_create(nfeatures=1000)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING)
        
        # 恢复按形状分类的子库
        self.static_lib = {'Large': {}, 'Medium': {}, 'Small': {}}
        self.user_memory = {} 
        
        os.makedirs(config.CACHE_DIR, exist_ok=True)
        self._load_all_libraries()

    def _load_all_libraries(self):
        if os.path.exists(config.STATIC_LIB_FILE):
            try:
                with open(config.STATIC_LIB_FILE, "rb") as f:
                    self.static_lib = pickle.load(f)
                # 检查数据结构
                if 'Small' not in self.static_lib:
                    self._build_static_library()
                return
            except: 
                pass
        self._build_static_library()

        if os.path.exists(config.USER_MEMORY_FILE):
            try: 
                with open(config.USER_MEMORY_FILE, "rb") as f: 
                    self.user_memory = pickle.load(f)
            except: 
                self.user_memory = {}

    def _build_static_library(self):
        logger.info("正在根据宽高比逻辑构建特征库...")
        self.static_lib = {'Large': {}, 'Medium': {}, 'Small': {}}
        with open(config.ITEMS_DB_PATH, 'r', encoding='utf-8') as f:
            db = json.load(f)

        for item in db:
            item_id = item.get('id', '').strip()
            # 从 JSON 中读取尺寸分类 (应包含 Large/Medium/Small)
            size_cat = item.get('size', '').split('/')[0].strip()
            
            path = self._find_img_path(item_id)
            if not path or size_cat not in self.static_lib: continue
            
            img_gray = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if img_gray is None: continue

            kp, des = self.orb.detectAndCompute(img_gray, None)
            if des is not None:
                self.static_lib[size_cat][item_id] = {
                    'orb_des': des, 
                    'kp_count': len(kp)
                }
        
        with open(config.STATIC_LIB_FILE, "wb") as f:
            pickle.dump(self.static_lib, f)
        logger.success("特征库构建完成。")

    def _find_img_path(self, item_id):
        for ext in ['.png', '.jpg', '.webp']:
            p = os.path.join(config.CARD_IMAGES_DIR, f"{item_id}{ext}")
            if os.path.exists(p): return p
        return None

    def match(self, target_img, size_cat):
        """ 
        全量比对指定尺寸子库：完全对齐 Rust 旧逻辑 
        """
        if size_cat not in self.static_lib:
            logger.error(f"无效的尺寸分类: {size_cat}")
            return []

        target_gray = cv2.cvtColor(target_img, cv2.COLOR_BGR2GRAY)
        t_kp, t_des = self.orb.detectAndCompute(target_gray, None)
        if t_des is None or len(t_kp) == 0: 
            return []

        final_res = []
        lib = self.static_lib[size_cat] # 只在对应的形状库里找
        
        for cid, static_data in lib.items():
            sources = [static_data]
            if cid in self.user_memory:
                sources.extend(self.user_memory[cid])
            
            best_score = 0
            for src in sources:
                matches = self.bf.knnMatch(t_des, src['orb_des'], k=2)
                good = 0
                for m_n in matches:
                    if len(m_n) == 2:
                        m, n = m_n
                        if m.distance < config.ORB_RATIO * n.distance:
                            good += 1
                
                denom = max(1, min(len(t_kp), src['kp_count']))
                score = float(good) / denom
                if score > best_score: best_score = score
            
            if best_score >= config.ORB_MATCH_THRESHOLD:
                final_res.append((cid, best_score))

        return sorted(final_res, key=lambda x: x[1], reverse=True)[:1]