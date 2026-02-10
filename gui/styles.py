# gui/styles.py

# --- 1. 颜色常量 (Colors) ---
COLOR_GOLD           = "#f59e0b"    # 现代琥珀金色
COLOR_GOLD_DARK      = "#d97706"    # 深琥珀色
COLOR_GOLD_HOVER     = "#fbbf24"    # 浅琥珀色（悬停）
COLOR_BG_MAIN        = "#241f1c"    # 深褐色基调
COLOR_BG_DARK        = "#0f0e0d"    # 接近纯黑
COLOR_BG_NAV         = "rgba(10, 10, 10, 0.95)"  # 侧边栏背景
COLOR_BG_CONTENT     = "#121212"    # 内容区背景
COLOR_TEXT_PRIMARY   = "#f0f0f0"
COLOR_TEXT_DIM       = "#888888"
COLOR_BORDER_SUBTLE  = "rgba(245, 158, 11, 0.15)"  # 更新边框颜色

# --- 2. 尺寸常量 (Dimensions - 基础值，未缩放) ---
NAV_WIDTH_COLLAPSED = 65
NAV_WIDTH_EXPANDED  = 200
TITLE_BAR_HEIGHT    = 50
WINDOW_RADIUS       = 12

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

def get_sidebar_style(scale=1.0):
    """根据缩放系数生成动态 QSS - Mobalytics 风格"""
    f_title = int(14 * scale)
    f_btn = int(13 * scale)
    radius = int(16 * scale)
    title_h = int(50 * scale)
    nav_w_collapsed = int(60 * scale)

    return f"""
    /* 全局基础：强制指定中文字体 */
    QWidget {{
        color: {COLOR_TEXT_PRIMARY};
        font-family: "Segoe UI", "Microsoft YaHei UI", "Inter", sans-serif;
        font-weight: 500;
    }}

    /* 主外壳 */
    #SidebarMain {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(18, 18, 20, 0.98),
            stop:1 rgba(10, 10, 12, 0.98));
        border: 1px solid rgba(255, 204, 0, 0.1);
        border-radius: {radius}px;
    }}

    /* 顶部标题栏 */
    #TitleBar {{
        background: rgba(15, 15, 17, 0.95);
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        border-top-left-radius: {radius}px;
        border-top-right-radius: {radius}px;
    }}

    #AppTitle {{
        color: rgba(255, 255, 255, 0.95);
        font-size: {f_title}px;
        font-weight: 700;
        letter-spacing: 2px;
    }}

    /* 语言切换按钮 */
    #LangButton {{
        background: rgba(40, 40, 45, 0.8);
        color: #cccccc;
        font-size: {int(10*scale)}px;
        font-weight: 600;
        border: 1px solid rgba(255, 204, 0, 0.2);
        border-radius: 6px;
    }}
    #LangButton:hover {{
        background: rgba(50, 50, 55, 0.9);
        border: 1px solid rgba(255, 204, 0, 0.4);
        color: #ffcc00;
    }}

    /* 侧边栏 - 悬浮层 */
    #NavRail {{
        background: {COLOR_BG_NAV};
        border-right: 1px solid rgba(255, 204, 0, 0.08);
        border-bottom-left-radius: {radius}px;
    }}

    /* ✅ 右下角调整大小手柄 */
    QSizeGrip {{
        background: transparent;
        width: 20px;
        height: 20px;
        image: url(none);  /* 移除默认图标 */
    }}
    
    QSizeGrip:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 rgba(255, 204, 0, 0.1),
            stop:1 rgba(255, 204, 0, 0.3));
        border-top-left-radius: 4px;
    }}

    /* 导航按钮 */
    .NavButton {{
        background: transparent;
        border: none;
        border-left: 3px solid transparent;  /* 预留左侧边框位置 */
        color: {COLOR_TEXT_DIM};  /* 默认白色，与图标颜色一致 */
        font-size: {int(13*scale)}px;  /* 文字字体大小 */
        font-weight: 600;
        text-align: left;
        padding-left: {int(8*scale)}px;  /* 减少左侧内边距，让图标更靠左 */
        border-radius: {int(8*scale)}px;
        margin: 0px {int(6*scale)}px;
    }}

    .NavButton:hover {{
        color: white;
        background: rgba(255, 255, 255, 0.05);
    }}

    /* 激活状态：金色左边框 + 渐变背景 */
    .NavButton:checked {{
        color: {COLOR_GOLD};  /* 选中时文字变金色 */
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 rgba(255, 204, 0, 0.15),
            stop:1 transparent);
        border-left: 3px solid {COLOR_GOLD};
    }}

    #CollapseBtn {{
        color: rgba(255, 255, 255, 0.5);
        background: transparent;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 6px;
        margin-right: 10px;
    }}

    QToolTip {{
        background-color: #000;
        color: {COLOR_GOLD};
        border: 1px solid {COLOR_GOLD};
        padding: 5px;
        border-radius: 4px;
    }}
    
    /* === 设置页面样式 === */
    QScrollArea {{
        background: transparent;
        border: none;
    }}
    
    QScrollArea > QWidget > QWidget {{
        background: transparent;
    }}
    
    #PageTitle {{
        color: {COLOR_TEXT_PRIMARY};
        padding-bottom: {int(10*scale)}px;
        border-bottom: 2px solid {COLOR_BORDER_SUBTLE};
    }}
    
    #SettingGroup {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(245, 158, 11, 0.08),
            stop:1 rgba(245, 158, 11, 0.02));
        border: 1px solid {COLOR_BORDER_SUBTLE};
        border-radius: {int(12*scale)}px;
        padding: {int(5*scale)}px;
    }}
    
    #SettingDesc {{
        color: {COLOR_TEXT_DIM};
        font-size: {int(11*scale)}px;
        padding-bottom: {int(5*scale)}px;
    }}
    
    #ScaleButton {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(245, 158, 11, 0.15),
            stop:1 rgba(245, 158, 11, 0.08));
        color: {COLOR_GOLD};
        border: 2px solid {COLOR_BORDER_SUBTLE};
        border-radius: {int(8*scale)}px;
        font-size: {int(20*scale)}px;
        font-weight: bold;
    }}
    
    #ScaleButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(245, 158, 11, 0.25),
            stop:1 rgba(245, 158, 11, 0.15));
        border-color: {COLOR_GOLD};
    }}
    
    #ScaleButton:pressed {{
        background: rgba(245, 158, 11, 0.35);
    }}
    
    #ScaleValue {{
        color: {COLOR_GOLD};
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid {COLOR_BORDER_SUBTLE};
        border-radius: {int(6*scale)}px;
        padding: {int(8*scale)}px;
    }}
    
    #PresetButton {{
        background: rgba(255, 255, 255, 0.05);
        color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_BORDER_SUBTLE};
        border-radius: {int(6*scale)}px;
        padding: {int(6*scale)}px {int(12*scale)}px;
        font-size: {int(11*scale)}px;
    }}
    
    #PresetButton:hover {{
        background: rgba(245, 158, 11, 0.15);
        border-color: {COLOR_GOLD};
        color: {COLOR_GOLD};
    }}
    
    #PresetButton:pressed {{
        background: rgba(245, 158, 11, 0.25);
    }}
    
    #LanguageRadio {{
        color: {COLOR_TEXT_PRIMARY};
        font-size: {int(12*scale)}px;
        spacing: {int(8*scale)}px;
    }}
    
    #LanguageRadio::indicator {{
        width: {int(18*scale)}px;
        height: {int(18*scale)}px;
        border-radius: {int(9*scale)}px;
        border: 2px solid {COLOR_BORDER_SUBTLE};
        background: transparent;
    }}
    
    #LanguageRadio::indicator:checked {{
        background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
            fx:0.5, fy:0.5,
            stop:0 {COLOR_GOLD},
            stop:0.6 {COLOR_GOLD},
            stop:0.7 transparent);
        border-color: {COLOR_GOLD};
    }}
    
    #LanguageRadio:hover {{
        color: {COLOR_GOLD};
    }}
    
    #CollapseCheckbox {{
        color: {COLOR_TEXT_PRIMARY};
        font-size: {int(12*scale)}px;
        spacing: {int(8*scale)}px;
    }}
    
    #CollapseCheckbox::indicator {{
        width: {int(20*scale)}px;
        height: {int(20*scale)}px;
        border-radius: {int(4*scale)}px;
        border: 2px solid {COLOR_BORDER_SUBTLE};
        background: transparent;
    }}
    
    #CollapseCheckbox::indicator:checked {{
        background: {COLOR_GOLD};
        border-color: {COLOR_GOLD};
        image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTMuMzMzMyA0TDYgMTEuMzMzM0wyLjY2NjY3IDgiIHN0cm9rZT0iYmxhY2siIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+PC9zdmc+);
    }}
    
    #CollapseCheckbox:hover {{
        color: {COLOR_GOLD};
    }}
    
    #DelaySpinbox {{
        background: rgba(255, 255, 255, 0.05);
        color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_BORDER_SUBTLE};
        border-radius: {int(6*scale)}px;
        padding: {int(6*scale)}px;
        font-size: {int(12*scale)}px;
    }}
    
    #DelaySpinbox:focus {{
        border-color: {COLOR_GOLD};
    }}
    
    #DelaySpinbox::up-button, #DelaySpinbox::down-button {{
        background: rgba(245, 158, 11, 0.1);
        border: none;
        border-radius: {int(3*scale)}px;
        width: {int(16*scale)}px;
    }}
    
    #DelaySpinbox::up-button:hover, #DelaySpinbox::down-button:hover {{
        background: rgba(245, 158, 11, 0.2);
    }}
    
    #DelaySpinbox::up-arrow {{
        image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1zbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMyA4TDYgNUw5IDgiIHN0cm9rZT0iI2Y1OWUwYiIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjwvc3ZnPg==);
        width: {int(12*scale)}px;
        height: {int(12*scale)}px;
    }}
    
    #DelaySpinbox::down-arrow {{
        image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1zbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNOSA1TDYgOEwzIDUiIHN0cm9rZT0iI2Y1OWUwYiIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjwvc3ZnPg==);
        width: {int(12*scale)}px;
        height: {int(12*scale)}px;
    }}
    
    QSlider::groove:horizontal {{
        height: {int(6*scale)}px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: {int(3*scale)}px;
    }}
    
    QSlider::handle:horizontal {{
        width: {int(18*scale)}px;
        height: {int(18*scale)}px;
        margin: {int(-6*scale)}px 0;
        background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
            stop:0 {COLOR_GOLD},
            stop:0.8 {COLOR_GOLD},
            stop:1 {COLOR_GOLD_DARK});
        border: 2px solid {COLOR_GOLD_HOVER};
        border-radius: {int(9*scale)}px;
    }}
    
    QSlider::handle:horizontal:hover {{
        background: {COLOR_GOLD_HOVER};
    }}
    
    QSlider::sub-page:horizontal {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLOR_GOLD_DARK},
            stop:1 {COLOR_GOLD});
        border-radius: {int(3*scale)}px;
    }}
    
    {SCROLLBAR_STYLE}
    """