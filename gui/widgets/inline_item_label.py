"""
通用的内联物品标签组件
用于在各种界面中显示物品图片
"""
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from utils.image_loader import ImageLoader, CardSize


class InlineItemLabel(QLabel):
    """
    内联物品标签 - 显示带边框的物品图片
    可以指定大小、边框颜色等
    """
    
    def __init__(self, item_id: str, tier_color: str = "#555555", 
                 content_scale: float = 1.0, card_size=CardSize.SMALL, 
                 parent=None, clickable: bool = False):
        """
        Args:
            item_id: 物品ID
            tier_color: 边框颜色
            content_scale: 缩放比例
            card_size: 卡牌尺寸 (CardSize.SMALL/MEDIUM/LARGE)
            parent: 父组件
            clickable: 是否可点击（显示手型光标）
        """
        super().__init__(parent)
        self.item_id = item_id
        self.tier_color = tier_color
        self.content_scale = content_scale
        
        # 应用缩放比例到图片尺寸
        base_width = int(40 * content_scale)  # 基础宽度40px（小型卡）
        border_w = max(2, int(3 * content_scale))
        
        # 根据卡牌尺寸决定宽度 - 1:2:3比例
        if card_size == CardSize.SMALL:
            img_w = base_width  # 40px (1倍)
            img_h = base_width  # 保持正方形
        elif card_size == CardSize.LARGE:
            img_w = base_width * 3  # 120px (3倍)
            img_h = base_width * 3  # 保持正方形
        else:  # MEDIUM
            img_w = base_width * 2  # 80px (2倍)
            img_h = base_width * 2  # 保持正方形
        
        # 给 QLabel 留出边框的额外像素
        total_w = img_w + border_w * 2
        total_h = img_h + border_w * 2
        self.setFixedSize(total_w, total_h)
        
        # 使用样式化边框
        self.setStyleSheet(f"border: {border_w}px solid {tier_color}; border-radius: 6px; background: transparent;")
        
        # 加载卡牌图片
        pix = ImageLoader.load_card_image(item_id, card_size, height=img_h, with_border=False)
        if not pix.isNull():
            scaled = pix.scaled(img_w, img_h, Qt.AspectRatioMode.KeepAspectRatio, 
                              Qt.TransformationMode.SmoothTransformation)
            self.setPixmap(scaled)
        
        # 设置光标
        if clickable:
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
