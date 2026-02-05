"""
图片加载工具 (Image Loader Utility)
提供统一的图片加载、叠加、缩放功能
"""
from PySide6.QtGui import QPixmap, QPainter, QPainterPath
from PySide6.QtCore import Qt, QSize
import os


class CardSize:
    """卡牌尺寸类型"""
    SMALL = "small"   # 小型：宽度是高度的 0.5 倍
    MEDIUM = "medium" # 中型：宽高 1:1
    LARGE = "large"   # 大型：宽度是高度的 1.5 倍


class ImageLoader:
    """图片加载器 - 统一的图片处理工具"""
    
    @staticmethod
    def load_monster_image(monster_name_zh: str, size: int = 70, 
                          with_border: bool = True) -> QPixmap:
        """
        加载怪物图片（bg + char 叠加）
        
        Args:
            monster_name_zh: 怪物中文名
            size: 图片尺寸（正方形）
            with_border: 是否添加黄色圆形边框
        
        Returns:
            QPixmap: 合成后的图片
        """
        bg_path = f"assets/images/monster_bg/{monster_name_zh}.webp"
        char_path = f"assets/images/monster_char/{monster_name_zh}.webp"
        
        # 检查文件是否存在
        if not os.path.exists(bg_path) or not os.path.exists(char_path):
            return ImageLoader._create_placeholder(size, with_border)
        
        # 加载图片
        bg_pixmap = QPixmap(bg_path)
        char_pixmap = QPixmap(char_path)
        
        if bg_pixmap.isNull() or char_pixmap.isNull():
            return ImageLoader._create_placeholder(size, with_border)
        
        # 叠加图片
        result = ImageLoader._overlay_images(bg_pixmap, char_pixmap, size, size)
        
        # 添加圆形边框
        if with_border:
            result = ImageLoader._add_circular_border(result, "#f59e0b", 2)
        
        return result
    
    @staticmethod
    def load_skill_image(skill_id: str, size: int = 60, 
                        with_border: bool = True) -> QPixmap:
        """
        加载技能图片
        
        Args:
            skill_id: 技能ID
            size: 图片尺寸（正方形）
            with_border: 是否添加黄色边框
        
        Returns:
            QPixmap: 技能图片
        """
        skill_path = f"assets/images/skill/{skill_id}.webp"
        
        if not os.path.exists(skill_path):
            return ImageLoader._create_placeholder(size, with_border)
        
        pixmap = QPixmap(skill_path)
        if pixmap.isNull():
            return ImageLoader._create_placeholder(size, with_border)
        
        # 缩放到指定尺寸
        scaled = pixmap.scaled(size, size, 
                              Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
        
        # 添加圆角边框
        if with_border:
            scaled = ImageLoader._add_rounded_border(scaled, "#f59e0b", 2, 8)
        
        return scaled
    
    @staticmethod
    def load_card_image(card_id: str, card_size: str = CardSize.MEDIUM, 
                       height: int = 80, with_border: bool = True) -> QPixmap:
        """
        加载卡牌图片（支持小中大三种尺寸比例）
        
        Args:
            card_id: 卡牌ID
            card_size: 卡牌尺寸类型（small/medium/large）
            height: 卡牌高度（宽度根据尺寸类型自动计算）
            with_border: 是否添加边框
        
        Returns:
            QPixmap: 卡牌图片
        """
        card_path = f"assets/images/card/{card_id}.webp"
        
        if not os.path.exists(card_path):
            # 计算宽度
            width = ImageLoader._calculate_card_width(height, card_size)
            return ImageLoader._create_placeholder(width, with_border, height)
        
        pixmap = QPixmap(card_path)
        if pixmap.isNull():
            width = ImageLoader._calculate_card_width(height, card_size)
            return ImageLoader._create_placeholder(width, with_border, height)
        
        # 计算宽度
        width = ImageLoader._calculate_card_width(height, card_size)
        
        # 缩放到指定尺寸
        scaled = pixmap.scaled(width, height,
                              Qt.AspectRatioMode.IgnoreAspectRatio,  # 强制使用指定比例
                              Qt.TransformationMode.SmoothTransformation)
        
        # 添加圆角边框
        if with_border:
            # 卡牌使用绿色边框
            scaled = ImageLoader._add_rounded_border(scaled, "#64c864", 2, 6)
        
        return scaled
    
    @staticmethod
    def _calculate_card_width(height: int, card_size: str) -> int:
        """
        根据卡牌类型计算宽度
        
        - small: 宽度 = 高度 * 0.5
        - medium: 宽度 = 高度 * 1.0
        - large: 宽度 = 高度 * 1.5
        """
        if card_size == CardSize.SMALL:
            return int(height * 0.5)
        elif card_size == CardSize.LARGE:
            return int(height * 1.5)
        else:  # MEDIUM
            return height
    
    @staticmethod
    def _overlay_images(bg: QPixmap, fg: QPixmap, width: int, height: int) -> QPixmap:
        """
        叠加两张图片（背景 + 前景）
        
        Args:
            bg: 背景图片
            fg: 前景图片
            width: 目标宽度
            height: 目标高度
        
        Returns:
            QPixmap: 叠加后的图片
        """
        # 创建画布
        canvas = QPixmap(width, height)
        canvas.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # 缩放背景图
        bg_scaled = bg.scaled(width, height,
                             Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                             Qt.TransformationMode.SmoothTransformation)
        
        # 缩放前景图
        fg_scaled = fg.scaled(width, height,
                             Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                             Qt.TransformationMode.SmoothTransformation)
        
        # 居中裁剪并绘制背景
        x_offset = (bg_scaled.width() - width) // 2
        y_offset = (bg_scaled.height() - height) // 2
        painter.drawPixmap(0, 0, bg_scaled, x_offset, y_offset, width, height)
        
        # 居中裁剪并绘制前景
        x_offset = (fg_scaled.width() - width) // 2
        y_offset = (fg_scaled.height() - height) // 2
        painter.drawPixmap(0, 0, fg_scaled, x_offset, y_offset, width, height)
        
        painter.end()
        
        return canvas
    
    @staticmethod
    def _add_circular_border(pixmap: QPixmap, color: str, border_width: int) -> QPixmap:
        """
        为图片添加圆形边框
        
        Args:
            pixmap: 原始图片
            color: 边框颜色（hex）
            border_width: 边框宽度
        
        Returns:
            QPixmap: 带边框的图片
        """
        from PySide6.QtGui import QPen, QColor
        
        size = pixmap.width()  # 假设是正方形
        result = QPixmap(size, size)
        result.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(result)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 创建圆形路径
        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        
        # 裁剪为圆形
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        
        # 绘制边框
        painter.setClipping(False)
        pen = QPen(QColor(color))
        pen.setWidth(border_width)
        painter.setPen(pen)
        painter.drawEllipse(border_width // 2, border_width // 2, 
                           size - border_width, size - border_width)
        
        painter.end()
        
        return result
    
    @staticmethod
    def _add_rounded_border(pixmap: QPixmap, color: str, border_width: int, 
                           radius: int) -> QPixmap:
        """
        为图片添加圆角矩形边框
        
        Args:
            pixmap: 原始图片
            color: 边框颜色（hex）
            border_width: 边框宽度
            radius: 圆角半径
        
        Returns:
            QPixmap: 带边框的图片
        """
        from PySide6.QtGui import QPen, QColor
        
        width = pixmap.width()
        height = pixmap.height()
        
        result = QPixmap(width, height)
        result.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(result)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 创建圆角矩形路径
        path = QPainterPath()
        path.addRoundedRect(0, 0, width, height, radius, radius)
        
        # 裁剪为圆角矩形
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        
        # 绘制边框
        painter.setClipping(False)
        pen = QPen(QColor(color))
        pen.setWidth(border_width)
        painter.setPen(pen)
        painter.drawRoundedRect(border_width // 2, border_width // 2,
                               width - border_width, height - border_width,
                               radius, radius)
        
        painter.end()
        
        return result
    
    @staticmethod
    def _create_placeholder(width: int, with_border: bool = True, 
                           height: int = None) -> QPixmap:
        """
        创建占位图片
        
        Args:
            width: 宽度
            with_border: 是否有边框
            height: 高度（如果为 None，则等于 width）
        
        Returns:
            QPixmap: 占位图片
        """
        from PySide6.QtGui import QColor, QBrush
        
        if height is None:
            height = width
        
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 填充半透明背景
        painter.setBrush(QBrush(QColor(40, 40, 40, 200)))
        painter.setPen(Qt.PenStyle.NoPen)
        
        if width == height:  # 正方形 - 使用圆形
            painter.drawEllipse(0, 0, width, height)
        else:  # 矩形 - 使用圆角矩形
            painter.drawRoundedRect(0, 0, width, height, 6, 6)
        
        painter.end()
        
        return pixmap


# 便捷函数
def load_monster_avatar(monster_name_zh: str, size: int = 70) -> QPixmap:
    """加载怪物头像（带圆形边框）"""
    return ImageLoader.load_monster_image(monster_name_zh, size, with_border=True)


def load_skill_icon(skill_id: str, size: int = 60) -> QPixmap:
    """加载技能图标（带边框）"""
    return ImageLoader.load_skill_image(skill_id, size, with_border=True)


def load_item_card(item_id: str, item_size: str, height: int = 80) -> QPixmap:
    """加载物品卡牌（带边框）"""
    return ImageLoader.load_card_image(item_id, item_size, height, with_border=True)
