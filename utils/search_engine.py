import json
from rapidfuzz import process, fuzz, utils
from loguru import logger

class FuzzySearcher:
    def __init__(self, items_db_path):
        """
        初始化搜索引擎
        :param items_db_path: JSON 数据库路径
        """
        try:
            with open(items_db_path, 'r', encoding='utf-8') as f:
                self.items_db = json.load(f)
            
            self.name_to_id = {}
            
            # 判断数据库类型
            if isinstance(self.items_db, list):
                # 物品数据库 (List of Dicts)
                # item['name_cn'] -> item['id']
                for item in self.items_db:
                    name = item.get('name_cn', '')
                    item_id = item.get('id', '')
                    if name and item_id:
                        self.name_to_id[name] = item_id
            
            elif isinstance(self.items_db, dict):
                # 怪物数据库 (Dict of Dicts)
                # key (中文名) -> key (作为ID)
                for key, data in self.items_db.items():
                    # 优先使用 name_zh，如果不存在则使用 key
                    name = data.get('name_zh', key)
                    # 对于怪物，我们用 key 作为唯一标识符
                    self.name_to_id[name] = key

            # 提取所有可搜索的名字列表
            self.all_names = list(self.name_to_id.keys())
            
            logger.info(f"FuzzySearcher 初始化成功，已加载 {len(self.all_names)} 条条目")
        except Exception as e:
            logger.error(f"FuzzySearcher 加载数据库失败: {e}")
            self.all_names = []

    def find_best_match(self, query, threshold=60):
        """
        寻找最匹配的 ID (用于 OCR 确权)
        :param query: OCR 识别出的原始文本 (如 "沉重 农贸集市")
        :param threshold: 分数阈值 0-100
        :return: 匹配到的 item_id 或 None
        """
        if not query or not self.all_names:
            return None

        # 核心算法说明：
        # 1. fuzz.WRatio: 综合评估相似度 (对错别字容忍度高)
        # 2. fuzz.partial_ratio: 部分匹配 (用于解决 "沉重农贸集市" 包含 "农贸集市" 的情况)
        
        # 尝试直接匹配
        res = process.extractOne(
            query, 
            self.all_names, 
            scorer=fuzz.WRatio,
            processor=utils.default_process # 自动转小写、去标点
        )

        if res and res[1] >= threshold:
            # 检查是否有更精准的部分匹配 (针对前缀)
            partial_res = process.extractOne(query, self.all_names, scorer=fuzz.partial_ratio)
            
            # 如果部分匹配得分极高 (比如 100)，说明它是带前缀的正确答案
            final_res = partial_res if partial_res[1] > res[1] else res
            
            matched_name = final_res[0]
            logger.debug(f"模糊匹配命中: {query} -> {matched_name} (Score: {final_res[1]})")
            return self.name_to_id[matched_name]
        
        return None

    def search_wiki(self, query, limit=10):
        """
        搜索百科 (用于用户手动输入搜索)
        :param query: 用户输入内容
        :param limit: 返回结果数量
        :return: 匹配到的完整 item 对象列表
        """
        if not query:
            return []

        # 获取前 N 个最相似的名字
        results = process.extract(
            query, 
            self.all_names, 
            scorer=fuzz.WRatio, 
            limit=limit
        )

        matched_items = []
        for name, score, index in results:
            if score > 30: # 百科搜索门槛可以设低一点，让结果更丰富
                item_id = self.name_to_id[name]
                # 找到原始 item 数据
                item_data = next((i for i in self.items_db if i['id'] == item_id), None)
                if item_data:
                    matched_items.append(item_data)
        
        return matched_items