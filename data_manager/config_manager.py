import json
import os
from loguru import logger

class ConfigManager:
    def __init__(self, config_path="user_data/settings.json"):
        self.path = config_path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.settings = self.load()

    def load(self):
        if os.path.exists(self.path):
            with open(self.path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "yolo_fps": 10,
            "best_ocr": "Windows_Native",
            "preferred_provider": "CPUExecutionProvider"
        }

    def save(self, new_settings):
        self.settings.update(new_settings)
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=4, ensure_ascii=False)
        logger.info(f"💾 用户配置已更新至: {self.path}")