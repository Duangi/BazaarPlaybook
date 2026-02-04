# gui/styles.py

# --- 颜色常量 (参考你的 CSS) ---
COLOR_GOLD = "#ffcd19"        # 核心金
COLOR_DARK_GOLD = "#d4af37"   # 深金/古铜
COLOR_MAIN_BG = "#2b2621"     # 酒馆褐
COLOR_DEEP_BG = "#1e1c19"     # 底部黑
COLOR_TEXT_WHITE = "#e6edf3"  # 文字白
COLOR_TEXT_GRAY = "#8b949e"   # 次要文字灰
COLOR_ACCENT = "rgba(255, 205, 25, 0.25)" # 强调色透明版

# --- 全局基础样式 ---
# 就像 CSS 的 reset.css，统一所有基础组件的外观
BASE_STYLE = f"""
QWidget {{
    background-color: transparent;
    color: {COLOR_TEXT_WHITE};
    font-family: "Microsoft YaHei", "微软雅黑";
}}

QLabel {{
    background: transparent;
}}

QPushButton {{
    border-radius: 6px;
    padding: 8px 16px;
    outline: none;
}}
"""

# --- 启动页专属样式 ---
START_WINDOW_STYLE = BASE_STYLE + f"""
#StartContainer {{
    background-color: {COLOR_MAIN_BG};
    border: 3px solid {COLOR_GOLD};
    border-radius: 16px;
}}

#AppTitle {{
    color: {COLOR_GOLD};
    font-size: 34px;
    font-weight: bold;
    letter-spacing: 5px;
}}

#BulletinBody {{
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid {COLOR_ACCENT};
    border-radius: 12px;
}}

#EnterBtn {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLOR_GOLD}, stop:1 {COLOR_DARK_GOLD});
    color: #1a1410;
    font-weight: bold;
    font-size: 18px;
}}

#EnterBtn:hover {{
    background-color: #ffdb4d;
}}
"""

# --- 灵动岛样式 (预留) ---
ISLAND_STYLE = f"""
#IslandFrame {{
    background-color: rgba(0, 0, 0, 0.85);
    border: 1px solid {COLOR_GOLD};
    border-radius: 20px;
}}
"""