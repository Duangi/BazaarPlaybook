# gui/styles.py

COLOR_GOLD = "#ffcc00"
COLOR_GOLD_HOVER = "#ffdb4d"
COLOR_BG_MAIN = "#241f1c"    # 更深一点的褐色
COLOR_BG_DARK = "#0f0e0d"    # 接近纯黑
COLOR_TEXT_PRIMARY = "#f0f0f0"
COLOR_TEXT_DIM = "#888888"

# 全局滚动条样式 - 圆润美观版
SCROLLBAR_STYLE = f"""
QScrollBar:vertical {{
    background: transparent;
    width: 14px;
    margin: 2px 2px 2px 2px;
}}
QScrollBar::handle:vertical {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(255, 204, 0, 0.25),
        stop:1 rgba(255, 204, 0, 0.35));
    border-radius: 7px;
    min-height: 30px;
    margin: 0px 2px;
}}
QScrollBar::handle:vertical:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(255, 204, 0, 0.45),
        stop:1 rgba(255, 204, 0, 0.55));
}}
QScrollBar::handle:vertical:pressed {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLOR_GOLD},
        stop:1 {COLOR_GOLD_HOVER});
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
    background: none;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 14px;
    margin: 2px 2px 2px 2px;
}}
QScrollBar::handle:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(255, 204, 0, 0.25),
        stop:1 rgba(255, 204, 0, 0.35));
    border-radius: 7px;
    min-width: 30px;
    margin: 2px 0px;
}}
QScrollBar::handle:horizontal:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(255, 204, 0, 0.45),
        stop:1 rgba(255, 204, 0, 0.55));
}}
QScrollBar::handle:horizontal:pressed {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {COLOR_GOLD},
        stop:1 {COLOR_GOLD_HOVER});
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
    background: none;
}}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: transparent;
}}
"""

GLOBAL_STYLE = f"""
QWidget {{
    color: {COLOR_TEXT_PRIMARY};
    font-family: "Segoe UI", "Microsoft YaHei UI";
}}
#MainFrame {{
    background-color: {COLOR_BG_MAIN};
    border: 2px solid {COLOR_GOLD};
    border-radius: 12px;
}}
{SCROLLBAR_STYLE}
"""

START_WINDOW_STYLE = GLOBAL_STYLE + f"""
#AppTitle {{
    color: {COLOR_GOLD};
    font-size: 52px;
    font-weight: 900;
    letter-spacing: 6px;
    margin-bottom: 5px;
}}
#AppSubtitle {{
    color: {COLOR_TEXT_DIM};
    font-size: 13px;
    font-weight: 500;
    letter-spacing: 4px;
    margin-bottom: 10px;
}}
#InfoCard {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(255, 204, 0, 0.05),
        stop:1 rgba(0, 0, 0, 0.3));
    border: 1px solid rgba(255, 204, 0, 0.2);
    border-radius: 12px;
}}
#Divider {{
    background-color: rgba(255, 204, 0, 0.2);
    border: none;
}}
#VersionText {{
    color: {COLOR_GOLD};
    font-size: 16px;
    font-weight: bold;
}}
#FeatureText {{
    color: {COLOR_TEXT_PRIMARY};
    font-size: 14px;
    line-height: 1.8;
}}
#DisclaimerText {{
    color: {COLOR_TEXT_DIM};
    font-size: 12px;
    font-style: italic;
}}
"""

DIAGNOSTICS_STYLE = GLOBAL_STYLE + f"""
#DiagHeader {{
    font-size: 32px;
    font-weight: 900;
    color: {COLOR_GOLD};
    border: none;
}}
#TaskPanel {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(0, 0, 0, 0.4),
        stop:1 rgba(0, 0, 0, 0.2));
    border: 1px solid rgba(255, 204, 0, 0.15);
    border-radius: 10px;
}}
#TaskTitle {{
    font-size: 16px;
    font-weight: bold;
    color: {COLOR_GOLD};
    margin-bottom: 10px;
}}
#TaskItem {{
    background: rgba(255, 204, 0, 0.03);
    border: 1px solid rgba(255, 204, 0, 0.1);
    border-radius: 8px;
    padding: 5px;
}}
#TaskItem[status="idle"] #StatusIndicator {{
    color: {COLOR_TEXT_DIM};
    font-size: 18px;
}}
#TaskItem[status="done"] {{
    background: rgba(255, 204, 0, 0.1);
    border-color: rgba(255, 204, 0, 0.3);
}}
#TaskItem[status="done"] #StatusIndicator {{
    color: {COLOR_GOLD};
    font-size: 18px;
}}
#TaskItem #TaskTitle {{
    color: {COLOR_TEXT_PRIMARY};
    font-size: 14px;
    font-weight: bold;
    margin: 0px;
}}
#TaskItem #TaskDesc {{
    color: {COLOR_TEXT_DIM};
    font-size: 11px;
    margin: 0px;
}}
#ConsolePanel {{
    background: transparent;
    border: none;
}}
#ConsoleHeader {{
    font-size: 14px;
    font-weight: bold;
    color: {COLOR_GOLD};
    border: none;
}}
#LogConsole {{
    background-color: {COLOR_BG_DARK};
    border: 1px solid rgba(255, 204, 0, 0.15);
    border-radius: 8px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 13px;
    color: #cccccc;
    padding: 12px;
    line-height: 1.5;
}}
#LogConsole QScrollBar:vertical {{
    width: 10px;
}}
#LogConsole QScrollBar::handle:vertical {{
    background: rgba(255, 204, 0, 0.4);
}}
"""