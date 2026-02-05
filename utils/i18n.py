"""
本地化管理器 (Internationalization Manager)
支持简体中文、繁体中文、英文切换
"""
import json
from typing import Dict, Any
from zhconv import convert  # pip install zhconv


class I18nManager:
    """本地化管理器"""
    
    # 支持的语言
    LANG_ZH_CN = "zh_CN"  # 简体中文
    LANG_ZH_TW = "zh_TW"  # 繁体中文
    LANG_EN = "en_US"     # 英文
    
    def __init__(self, default_lang="zh_CN"):
        self.current_lang = default_lang
        self._cache = {}  # 翻译缓存
    
    def set_language(self, lang: str):
        """设置当前语言"""
        if lang in [self.LANG_ZH_CN, self.LANG_ZH_TW, self.LANG_EN]:
            self.current_lang = lang
            self._cache.clear()  # 清除缓存
    
    def get_language(self) -> str:
        """获取当前语言"""
        return self.current_lang
    
    def translate(self, text: str, en_text: str = "") -> str:
        """
        翻译文本
        
        Args:
            text: 简体中文文本
            en_text: 英文文本（如果有）
        
        Returns:
            根据当前语言返回对应文本
        """
        if not text:
            return ""
        
        # 检查缓存
        cache_key = f"{self.current_lang}:{text}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = text
        
        if self.current_lang == self.LANG_EN and en_text:
            # 英文：使用提供的英文文本
            result = en_text
        elif self.current_lang == self.LANG_ZH_TW:
            # 繁体中文：简体转繁体
            result = self.to_traditional(text)
        # 简体中文：直接返回原文
        
        # 缓存结果
        self._cache[cache_key] = result
        return result
    
    @staticmethod
    def to_traditional(simplified: str) -> str:
        """简体转繁体"""
        try:
            return convert(simplified, 'zh-tw')
        except:
            # 如果 zhconv 不可用，手动转换常见字
            replacements = {
                '里': '裡', '发': '發', '台': '臺', '为': '為',
                '听': '聽', '万': '萬', '与': '與', '业': '業',
                '丛': '叢', '东': '東', '丝': '絲', '严': '嚴',
                '个': '個', '么': '麼', '义': '義', '之': '之',
                '乌': '烏', '书': '書', '买': '買', '乱': '亂',
                '争': '爭', '于': '於', '亏': '虧', '云': '雲',
                '亚': '亞', '产': '產', '亩': '畝', '享': '享',
                '仅': '僅', '从': '從', '仑': '侖', '仓': '倉',
                '代': '代', '们': '們', '以': '以', '仪': '儀',
                '价': '價', '众': '眾', '优': '優', '会': '會',
                '伛': '傴', '伞': '傘', '伟': '偉', '传': '傳',
                '伤': '傷', '伦': '倫', '伪': '偽', '休': '休',
                '众': '眾', '优': '優', '伙': '夥', '会': '會',
                '伤': '傷', '余': '餘', '佣': '傭', '体': '體',
                '何': '何', '佐': '佐', '佛': '佛', '作': '作',
                '你': '你', '佣': '傭', '佩': '佩', '佳': '佳',
                '使': '使', '侦': '偵', '供': '供', '依': '依',
                '侠': '俠', '侣': '侶', '侥': '僥', '侧': '側',
                '侨': '僑', '侩': '儈', '侪': '儕', '侬': '儂',
                '侮': '侮', '侯': '侯', '侵': '侵', '侶': '侶',
                '便': '便', '促': '促', '俄': '俄', '俊': '俊',
                '俎': '俎', '俏': '俏', '俐': '俐', '俑': '俑',
                '俗': '俗', '俘': '俘', '俚': '俚', '保': '保',
                '俦': '儔', '俨': '儼', '俩': '倆', '俪': '儷',
                '俫': '俫', '俬': '俬', '俭': '儉', '修': '修',
            }
            for s, t in replacements.items():
                simplified = simplified.replace(s, t)
            return simplified
    
    def t(self, zh_cn: str, en: str = "") -> str:
        """translate 的简写"""
        return self.translate(zh_cn, en)


# 全局单例
_i18n_instance = None

def get_i18n() -> I18nManager:
    """获取全局 I18n 实例"""
    global _i18n_instance
    if _i18n_instance is None:
        _i18n_instance = I18nManager()
    return _i18n_instance
