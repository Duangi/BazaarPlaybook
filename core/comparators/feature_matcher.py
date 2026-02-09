import os
import cv2
import pickle
import json
import time
import numpy as np
from loguru import logger
import config

class FeatureMatcher:
    def __init__(self):
        # 对齐 Rust 版 nfeatures=500
        logger.debug("FeatureMatcher: 正在初始化 ORB 引擎 (nfeatures=500)...")
        self.orb = cv2.ORB_create(nfeatures=500)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING)
        
        # 恢复按形状分类的子库
        self.static_lib = {'Large': {}, 'Medium': {}, 'Small': {}}
        self.monster_lib = {} # 怪物特征库
        self.user_memory = {} 
        
        os.makedirs(config.CACHE_DIR, exist_ok=True)
        self._load_all_libraries()

    def _load_all_libraries(self):
        logger.info("FeatureMatcher: 正在加载特征数据库...")
        
        # 1. 加载静态库 (Items)
        if os.path.exists(config.STATIC_LIB_FILE):
            try:
                with open(config.STATIC_LIB_FILE, "rb") as f:
                    self.static_lib = pickle.load(f)
                
                # 检查数据结构
                if 'Small' not in self.static_lib:
                    logger.warning("FeatureMatcher: 检测到旧版结构，准备重构静态库...")
                    self._build_static_library()
                else:
                    l_count = len(self.static_lib['Large'])
                    m_count = len(self.static_lib['Medium'])
                    s_count = len(self.static_lib['Small'])
                    logger.success(f"FeatureMatcher: Item特征库加载成功 (L:{l_count}, M:{m_count}, S:{s_count})")
            except Exception as e:
                logger.error(f"FeatureMatcher: 加载静态特征库失败: {e}")
                self._build_static_library()
        else:
            logger.info("FeatureMatcher: 静态库不存在，开始初次构建...")
            self._build_static_library()

        # 2. 加载怪物库 (Monsters)
        if os.path.exists(config.MONSTER_LIB_FILE):
             try:
                with open(config.MONSTER_LIB_FILE, "rb") as f:
                    self.monster_lib = pickle.load(f)
                logger.success(f"FeatureMatcher: Monster特征库加载成功 ({len(self.monster_lib)} monsters)")
             except Exception as e:
                logger.error(f"FeatureMatcher: 加载怪物特征库失败: {e}")
                self._build_monster_library()
        else:
             self._build_monster_library()

        # 3. 加载用户记忆库
        if os.path.exists(config.USER_MEMORY_FILE):
            try: 
                with open(config.USER_MEMORY_FILE, "rb") as f: 
                    self.user_memory = pickle.load(f)
                logger.success(f"FeatureMatcher: 用户记忆库加载成功 (包含 {len(self.user_memory)} 个条目)")
            except Exception as e:
                logger.error(f"FeatureMatcher: 加载用户记忆库失败: {e}")
                self.user_memory = {}

    def _build_static_library(self):
        start_time = time.perf_counter()
        logger.info("FeatureMatcher: 开始扫描数据库并提取 ORB 特征点...")
        
        self.static_lib = {'Large': {}, 'Medium': {}, 'Small': {}}
        try:
            with open(config.ITEMS_DB_PATH, 'r', encoding='utf-8') as f:
                db = json.load(f)
        except Exception as e:
            logger.critical(f"FeatureMatcher: 无法读取数据库文件 {config.ITEMS_DB_PATH}: {e}")
            return

        process_count = 0
        for item in db:
            item_id = item.get('id', '').strip()
            size_cat = item.get('size', '').split('/')[0].strip() # 'Small' / 'Medium' / 'Large'
            
            path = self._find_img_path(item_id)
            if not path or size_cat not in self.static_lib: 
                continue
            
            img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
            if img is None: 
                logger.warning(f"FeatureMatcher: 无法加载图片 -> {path}")
                continue

            kp, des = self.orb.detectAndCompute(img, None)
            if des is not None:
                self.static_lib[size_cat][item_id] = {
                    'orb_des': des, 
                    'kp_count': len(kp)
                }
                process_count += 1
        
        with open(config.STATIC_LIB_FILE, "wb") as f:
            pickle.dump(self.static_lib, f)
            
        cost = time.perf_counter() - start_time
        logger.success(f"FeatureMatcher: 特征库构建完成! 处理了 {process_count} 张卡牌，耗时: {cost:.2f}s")
    
    def _build_monster_library(self):
        """构建怪物特征库"""
        start_time = time.perf_counter()
        logger.info("FeatureMatcher: 开始构建怪物特征库...")
        self.monster_lib = {}
        
        if not os.path.exists(config.MONSTER_CHAR_DIR):
            logger.error(f"FeatureMatcher: 怪物图片目录不存在: {config.MONSTER_CHAR_DIR}")
            return

        count = 0
        
        for filename in os.listdir(config.MONSTER_CHAR_DIR):
            if filename.lower().endswith(('.webp', '.png', '.jpg')):
                path = os.path.join(config.MONSTER_CHAR_DIR, filename)
                name_id = os.path.splitext(filename)[0] # 文件名作为ID
                
                # 能够读取中文路径
                img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
                if img is None: continue
                
                kp, des = self.orb.detectAndCompute(img, None)
                if des is not None:
                    self.monster_lib[name_id] = {
                        'orb_des': des,
                        'kp_count': len(kp)
                    }
                    count += 1
        
        with open(config.MONSTER_LIB_FILE, "wb") as f:
            pickle.dump(self.monster_lib, f)
            
        logger.success(f"FeatureMatcher: 怪物库构建完成 ({count} units), 耗时: {time.perf_counter()-start_time:.2f}s")

    def _find_img_path(self, item_id):
        for ext in ['.png', '.jpg', '.webp']:
            p = os.path.join(config.CARD_IMAGES_DIR, f"{item_id}{ext}")
            if os.path.exists(p): 
                return p
        return None

    def match_monster_character(self, target_img):
        """匹配怪物角色图片"""
        match_start = time.perf_counter()
        
        target_gray = cv2.cvtColor(target_img, cv2.COLOR_BGR2GRAY)
        t_kp, t_des = self.orb.detectAndCompute(target_gray, None)
        num_target_kp = len(t_kp) if t_kp else 0
        
        if t_des is None or num_target_kp == 0:
            return []

        final_res = []
        for name, static_data in self.monster_lib.items():
            matches = self.bf.knnMatch(t_des, static_data['orb_des'], k=2)
            good = 0
            for m_n in matches:
                if len(m_n) == 2:
                    m, n = m_n
                    if m.distance < config.ORB_RATIO * n.distance:
                        good += 1
            
            denom = max(1, min(num_target_kp, static_data['kp_count']))
            score = float(good) / denom
            if score >= config.ORB_MATCH_THRESHOLD:
               final_res.append((name, score))

        sorted_res = sorted(final_res, key=lambda x: x[1], reverse=True)[:1]
        
        # Log (optional, avoid spam if called per frame)
        # if sorted_res:
        #    logger.debug(f"Monster Match: {sorted_res[0]}")

        return sorted_res

    def match(self, target_img, size_cat):
        """ 
        全量比对指定尺寸子库：完全对齐 Rust 旧逻辑 
        """
        match_start = time.perf_counter()
        
        if size_cat not in self.static_lib:
            logger.error(f"FeatureMatcher: 传入了无效的分类名 -> {size_cat}")
            return []

        # 1. 目标特征提取
        target_gray = cv2.cvtColor(target_img, cv2.COLOR_BGR2GRAY)
        t_kp, t_des = self.orb.detectAndCompute(target_gray, None)
        num_target_kp = len(t_kp) if t_kp else 0
        
        logger.debug(f"FeatureMatcher: 目标图 [{size_cat}] 特征提取完成, 特征点数: {num_target_kp}")
        
        if t_des is None or num_target_kp == 0: 
            logger.debug("FeatureMatcher: 目标图特征点为空，跳过比对")
            return []

        final_res = []
        lib = self.static_lib[size_cat] 
        logger.debug(f"FeatureMatcher: 正在比对 [{size_cat}] 库中的 {len(lib)} 个模板...")
        
        # 2. 全量暴力匹配
        for cid, static_data in lib.items():
            sources = [static_data]
            if cid in self.user_memory:
                sources.extend(self.user_memory[cid])
            
            best_score = 0
            for src in sources:
                # 对齐旧代码：knnMatch + Ratio Test
                matches = self.bf.knnMatch(t_des, src['orb_des'], k=2)
                good = 0
                for m_n in matches:
                    if len(m_n) == 2:
                        m, n = m_n
                        if m.distance < config.ORB_RATIO * n.distance:
                            good += 1
                
                # 对齐旧代码：归一化评分
                denom = max(1, min(num_target_kp, src['kp_count']))
                score = float(good) / denom
                if score > best_score: 
                    best_score = score
            
            if best_score >= config.ORB_MATCH_THRESHOLD:
                final_res.append((cid, best_score))

        # 3. 结果整理
        sorted_res = sorted(final_res, key=lambda x: x[1], reverse=True)[:1]
        
        duration = (time.perf_counter() - match_start) * 1000
        if sorted_res:
            res_id, res_score = sorted_res[0]
            logger.success(f"FeatureMatcher: 识别成功! ID: {res_id[:8]}... 得分: {res_score:.4f} 耗时: {duration:.2f}ms")
        else:
            logger.debug(f"FeatureMatcher: 无有效匹配 (低于阈值 {config.ORB_MATCH_THRESHOLD}), 耗时: {duration:.2f}ms")

        return sorted_res