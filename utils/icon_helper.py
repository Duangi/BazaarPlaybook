"""
图标辅助工具模块
提供 SVG 图标加载和颜色处理功能
"""

import re
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtCore import Qt, QSize
from PySide6.QtSvg import QSvgRenderer


def create_colored_svg_icon(svg_path, color="#888888", size=24):
    """
    创建指定颜色的 SVG 图标
    
    Args:
        svg_path: SVG 文件路径
        color: 图标颜色（十六进制格式，如 "#888888"）
        size: 图标尺寸（像素）
    
    Returns:
        QIcon: 渲染后的图标对象
    """
    try:
        # 读取 SVG 文件
        with open(svg_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        # 替换 SVG 中的所有颜色为目标颜色
        svg_content = _replace_all_colors(svg_content, color)
        
        # 渲染 SVG 到 QPixmap
        renderer = QSvgRenderer(svg_content.encode('utf-8'))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        return QIcon(pixmap)
    except Exception as e:
        print(f"[IconHelper] Error loading SVG icon from {svg_path}: {e}")
        # 返回空图标
        return QIcon()


def _replace_all_colors(svg_content, color):
    """
    彻底替换 SVG 中的所有颜色属性为指定颜色
    
    Args:
        svg_content: SVG 文件内容字符串
        color: 目标颜色（十六进制格式，如 "#ffffff"）
    
    Returns:
        str: 替换后的 SVG 内容
    """
    # 使用正则表达式替换所有 fill 属性（包括 fill="#xxx" 和 fill:xxx 样式）
    # 匹配 fill="任何颜色值"
    svg_content = re.sub(r'fill="[^"]*"', f'fill="{color}"', svg_content)
    
    # 匹配 stroke="任何颜色值"  
    svg_content = re.sub(r'stroke="[^"]*"', f'stroke="{color}"', svg_content)
    
    # 匹配 CSS 样式中的 fill:xxx;
    svg_content = re.sub(r'fill:\s*[^;"\}]+', f'fill:{color}', svg_content)
    
    # 匹配 CSS 样式中的 stroke:xxx;
    svg_content = re.sub(r'stroke:\s*[^;"\}]+', f'stroke:{color}', svg_content)
    
    # 替换 currentColor
    svg_content = svg_content.replace('currentColor', color)
    
    return svg_content


def load_icon_with_size(svg_path, size=24, color="#888888"):
    """
    加载 SVG 图标并设置尺寸
    
    Args:
        svg_path: SVG 文件路径
        size: 图标尺寸
        color: 图标颜色
    
    Returns:
        tuple: (QIcon, QSize) 图标对象和尺寸对象
    """
    icon = create_colored_svg_icon(svg_path, color, size)
    icon_size = QSize(size, size)
    return icon, icon_size

