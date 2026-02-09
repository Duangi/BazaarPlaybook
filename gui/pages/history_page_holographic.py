"""
历史战绩页面 - 全息卡片流设计 (Mobalytics/Blitz 级别)
极简、专业、高级感
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QScrollArea, QFrame, QGraphicsOpacityEffect, QLayout, QSizePolicy, QProgressBar)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize, Property, QPoint, QTimer, QThread, Signal
from PySide6.QtGui import QCursor, QPainter, QColor, QPainterPath, QPixmap, QIcon
from typing import Dict, List
import json
from pathlib import Path

from services.log_analyzer import LogAnalyzer
from utils.image_loader import ImageLoader, CardSize


class MatchCard(QFrame):
    """对局卡片 - 极简全息设计"""
    
    def __init__(self, session, game_number: int, items_db: dict, parent=None):
        super().__init__(parent)
        self.session = session
        self.game_number = game_number
        self.items_db = items_db
        self.is_expanded = False
        self.is_animating = False  # 动画锁，防止反复点击
        
        # ✅ 小局排序状态（True=从1到10，False=从10到1）
        self.rounds_ascending = True
        
        # 计算战绩
        battles = session.pvp_battles
        self.total_battles = len(battles)
        self.wins = sum(1 for b in battles if b.get('victory', False))
        self.losses = self.total_battles - self.wins
        
        # 颜色方案
        self.win_color = "#00ECC3"  # 薄荷绿/青色
        self.loss_color = "#F5503D"  # 暗玫瑰红
        self.ongoing_color = "#FFD700"  # 金色（正在进行）
        self.gold_color = "#D4AF37"  # 金色强调
        
        # 边框颜色：正在进行用金色，已完成根据胜负
        if not session.is_finished:
            self.border_color = self.ongoing_color  # 正在进行用金色
        else:
            # 信任游戏日志的victory状态，但同时显示实际胜场数供用户查看
            self.border_color = self.win_color if session.victory else self.loss_color
        
        self._init_ui()
        self._setup_animations()
        
    def _init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # 强制顶部对齐，防止垂直居中
        
        # 未展开状态的头部 (60-70px)
        self.header_widget = self._create_header()
        self.header_widget.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        main_layout.addWidget(self.header_widget, 0, Qt.AlignmentFlag.AlignTop)  # 明确顶部对齐
        
        # 展开状态的详情
        self.details_widget = self._create_details()
        self.details_widget.setVisible(False)
        self.details_widget.setMaximumHeight(0)
        self.details_widget.setMinimumHeight(0)
        # 设置裁切属性，确保内容被高度限制裁切
        self.details_widget.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        self.details_widget.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.2);
                border-radius: 0px;
            }
        """)
        main_layout.addWidget(self.details_widget, 0, Qt.AlignmentFlag.AlignTop)  # 明确顶部对齐
        
        # 卡片样式 - 极简黑金
        self.setStyleSheet(f"""
            MatchCard {{
                background-color: #1A1714;
                border: 1px solid rgba(212, 175, 55, 0.1);
                border-left: 4px solid {self.border_color};
                border-radius: 6px;
                margin-bottom: 8px;
            }}
        """)
        
    def _create_header(self) -> QWidget:
        """创建头部（未展开状态）60-70px 高"""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 12, 20, 12)
        header_layout.setSpacing(15)
        header.setFixedHeight(66)
        
        # 左侧区域
        left_section = QHBoxLayout()
        left_section.setSpacing(12)
        
        # 英雄头像 36x36px 圆形，1px 金边
        hero_avatar = QLabel()
        hero_avatar.setFixedSize(36, 36)
        hero_avatar.setStyleSheet(f"""
            QLabel {{
                border-radius: 18px;
                border: 1px solid {self.gold_color};
                background-color: rgba(0, 0, 0, 0.3);
                color: #666;
                font-size: 10px;
            }}
        """)
        hero_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_avatar.setScaledContents(True)
        
        # 加载英雄头像图片
        if self.session.hero:
            hero_name = self.session.hero.lower()
            hero_image_path = Path(__file__).parent.parent.parent / "assets" / "images" / "heroes" / f"{hero_name}.webp"
            
            if hero_image_path.exists():
                pixmap = QPixmap(str(hero_image_path))
                if not pixmap.isNull():
                    # 创建圆形遮罩
                    rounded_pixmap = QPixmap(36, 36)
                    rounded_pixmap.fill(Qt.GlobalColor.transparent)
                    
                    painter = QPainter(rounded_pixmap)
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                    
                    # 绘制圆形路径
                    path = QPainterPath()
                    path.addEllipse(0, 0, 36, 36)
                    painter.setClipPath(path)
                    
                    # 绘制图片
                    scaled_pixmap = pixmap.scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                    painter.drawPixmap(0, 0, scaled_pixmap)
                    painter.end()
                    
                    hero_avatar.setPixmap(rounded_pixmap)
                else:
                    hero_avatar.setText(self.session.hero[0].upper())
            else:
                hero_avatar.setText(self.session.hero[0].upper())
        else:
            hero_avatar.setText("?")
        left_section.addWidget(hero_avatar)
        
        # 胜负状态 + 时间戳（垂直排列）
        status_col = QVBoxLayout()
        status_col.setSpacing(2)
        
        # 🔥 信任游戏日志的session.victory，但显示实际胜场数
        victory_text = "胜利" if self.session.victory else "失败"
        status_label = QLabel(f"{victory_text} ({self.wins}胜)")
        status_label.setStyleSheet(f"""
            QLabel {{
                color: {self.border_color};
                font-weight: 900;
                font-size: 18px;
            }}
        """)
        status_col.addWidget(status_label)
        
        # 时间戳：小号灰色（精确到分钟）
        if hasattr(self.session, 'start_datetime') and self.session.start_datetime:
            time_text = self.session.start_datetime.strftime("%H:%M")
        elif self.session.start_time:
            # 从 HH:MM:SS.mmm 中提取 HH:MM
            time_text = self.session.start_time[:5] if len(self.session.start_time) >= 5 else self.session.start_time
        else:
            time_text = "未知时间"
        
        time_label = QLabel(time_text)
        time_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 11px;
            }
        """)
        status_col.addWidget(time_label)
        left_section.addLayout(status_col)
        
        header_layout.addLayout(left_section)
        
        # 中间弹性间距
        header_layout.addSpacing(30)
        
        # 核心战绩："10 胜 - 2 负"，金色数字
        stats_label = QLabel(f"{self.wins} 胜 - {self.losses} 负")
        stats_label.setStyleSheet(f"""
            QLabel {{
                color: {self.gold_color};
                font-size: 16px;
                font-weight: bold;
            }}
        """)
        header_layout.addWidget(stats_label)
        
        # 战绩流（小圆点/勾叉 12x12px）
        battle_flow = QWidget()
        flow_layout = QHBoxLayout(battle_flow)
        flow_layout.setContentsMargins(0, 0, 0, 0)
        flow_layout.setSpacing(4)
        
        battles = self.session.pvp_battles
        for i, battle in enumerate(battles[:15]):  # 最多显示15个
            is_win = battle.get('victory', False)
            dot = QLabel()
            dot.setFixedSize(12, 12)
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            if is_win:
                # 胜利：实心小圆点/勾
                dot.setStyleSheet(f"""
                    QLabel {{
                        background-color: {self.win_color};
                        border-radius: 6px;
                        color: #000;
                        font-size: 8px;
                        font-weight: bold;
                    }}
                """)
                dot.setText("✓")
            else:
                # 失败：空心圆点/叉
                dot.setStyleSheet(f"""
                    QLabel {{
                        background-color: transparent;
                        border: 2px solid {self.loss_color};
                        border-radius: 6px;
                        color: {self.loss_color};
                        font-size: 8px;
                        font-weight: bold;
                    }}
                """)
                dot.setText("✗")
            
            flow_layout.addWidget(dot)
        
        if len(battles) > 15:
            more_label = QLabel(f"+{len(battles) - 15}")
            more_label.setStyleSheet("""
                QLabel {
                    color: #666;
                    font-size: 10px;
                }
            """)
            flow_layout.addWidget(more_label)
        
        header_layout.addWidget(battle_flow)
        
        # 右侧弹性空间
        header_layout.addStretch()
        
        # 展开箭头 ∨
        self.expand_arrow = QLabel("∨")
        self.expand_arrow.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 14px;
            }
        """)
        header_layout.addWidget(self.expand_arrow)
        
        # 为头部添加点击事件处理
        header.mousePressEvent = lambda event: self._toggle_expand()
        
        return header
        
    def _create_details(self) -> QWidget:
        """创建详情面板（展开状态）"""
        # 使用 QFrame 代替 QWidget，更好的控制
        details = QFrame()
        details.setFrameShape(QFrame.Shape.NoFrame)
        
        # 设置尺寸策略，确保在动画过程中不会改变布局
        details.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed  # 固定高度策略
        )
        
        details_layout = QVBoxLayout(details)
        details_layout.setContentsMargins(20, 5, 20, 10)
        details_layout.setSpacing(8)
        details_layout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)  # 不自动调整
        
        # ✅ 添加排序控制按钮
        sort_row = QHBoxLayout()
        sort_row.addStretch()
        
        self.rounds_sort_btn = QPushButton("顺序：1→10")
        self.rounds_sort_btn.setFixedHeight(28)
        self.rounds_sort_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.rounds_sort_btn.clicked.connect(self._toggle_rounds_sort)
        self.rounds_sort_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 236, 195, 0.15);
                color: #00ECC3;
                border: 1px solid rgba(0, 236, 195, 0.3);
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(0, 236, 195, 0.25);
                border-color: #00ECC3;
            }
        """)
        sort_row.addWidget(self.rounds_sort_btn)
        details_layout.addLayout(sort_row)
        
        # 小局容器（用于动态更新排序）
        self.rounds_container = QWidget()
        self.rounds_layout = QVBoxLayout(self.rounds_container)
        self.rounds_layout.setContentsMargins(0, 0, 0, 0)
        self.rounds_layout.setSpacing(8)
        details_layout.addWidget(self.rounds_container)
        
        # 初始渲染小局
        self._render_rounds()
        
        return details
    
    def _render_rounds(self):
        """渲染小局列表（根据排序状态）"""
        # 清空现有内容
        while self.rounds_layout.count():
            item = self.rounds_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 获取排序后的战斗列表
        battles = self.session.pvp_battles
        if not self.rounds_ascending:
            battles = list(reversed(battles))
        
        # 渲染每一小局
        for idx, battle in enumerate(battles, 1):
            # 计算实际的round编号（不受排序影响）
            if self.rounds_ascending:
                round_num = idx
            else:
                round_num = len(self.session.pvp_battles) - idx + 1
            
            round_row = self._create_round_row(battle, round_num)
            self.rounds_layout.addWidget(round_row)
            
            # 分隔线（除了最后一个）
            if idx < len(battles):
                separator = QFrame()
                separator.setFrameShape(QFrame.Shape.HLine)
                separator.setStyleSheet("background-color: rgba(255, 255, 255, 0.05); max-height: 1px;")
                self.rounds_layout.addWidget(separator)
    
    def _toggle_rounds_sort(self):
        """切换小局排序"""
        self.rounds_ascending = not self.rounds_ascending
        
        # 更新按钮文本
        if self.rounds_ascending:
            self.rounds_sort_btn.setText("顺序：1→10")
        else:
            self.rounds_sort_btn.setText("顺序：10→1")
        
        # 重新渲染
        self._render_rounds()
    
    def _create_round_row(self, battle: Dict, round_num: int) -> QWidget:
        """创建小局行"""
        row = QWidget()
        row_layout = QVBoxLayout(row)
        row_layout.setContentsMargins(10, 8, 10, 8)
        row_layout.setSpacing(8)
        
        # 小局头部
        header_row = QHBoxLayout()
        header_row.setSpacing(12)
        
        # ROUND 1 - 全大写，极简等线字体
        round_label = QLabel(f"ROUND {round_num}")
        round_label.setStyleSheet(f"""
            QLabel {{
                color: {self.gold_color};
                font-size: 13px;
                font-weight: 600;
                letter-spacing: 1px;
                font-family: 'Consolas', 'Courier New', monospace;
            }}
        """)
        header_row.addWidget(round_label)
        
        # 本局状态图标（勾或叉）
        is_win = battle.get('victory', False)
        status_icon = QLabel("✓" if is_win else "✗")
        status_icon.setStyleSheet(f"""
            QLabel {{
                color: {self.win_color if is_win else self.loss_color};
                font-size: 14px;
                font-weight: bold;
            }}
        """)
        header_row.addWidget(status_icon)
        
        # 作战信息
        day_label = QLabel(f"第 {battle.get('day', '?')} 天")
        day_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 11px;
            }
        """)
        header_row.addWidget(day_label)
        
        # 显示战斗耗时
        duration = battle.get('duration')
        if duration:
            try:
                duration_float = float(duration)
                duration_label = QLabel(f"⏱ {duration_float:.1f}s")
                duration_label.setStyleSheet("""
                    QLabel {
                        color: #D4AF37;
                        font-size: 11px;
                        font-weight: 600;
                        background: rgba(212, 175, 55, 0.1);
                        padding: 2px 6px;
                        border-radius: 3px;
                    }
                """)
                header_row.addWidget(duration_label)
            except Exception as e:
                error_label = QLabel(f"[ERR: {e}]")
                error_label.setStyleSheet("QLabel { color: #ff0000; font-size: 9px; }")
                header_row.addWidget(error_label)
        
        header_row.addStretch()
        row_layout.addLayout(header_row)
        
        # 物品陈列区
        player_items = battle.get('player_items', [])
        if player_items:
            items_container = QWidget()
            items_layout = QHBoxLayout(items_container)
            items_layout.setContentsMargins(0, 0, 0, 0)
            items_layout.setSpacing(4)  # 紧凑的 4px 间距
            
            hand_items = [i for i in player_items if i.get('location') == 'Hand']
            
            for item in sorted(hand_items, key=lambda x: int(x.get('socket', 0)))[:12]:
                item_id = item.get('template_id', '')
                item_widget = self._create_item_icon(item_id)
                if item_widget:
                    items_layout.addWidget(item_widget)
            
            items_layout.addStretch()
            row_layout.addWidget(items_container)
        
        # 小局行样式
        row.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.2);
                border-radius: 4px;
            }
        """)
        
        return row
    
    def _create_item_icon(self, item_id: str) -> QWidget:
        """创建物品图标 - 1px 半透明白色边框"""
        if not item_id or item_id == "unknown":
            return None
        
        # 获取物品数据
        item_data = self.items_db.get(item_id)
        if not item_data:
            return None
        
        # 获取物品大小
        size_str = item_data.get("size", "Medium / 中")
        size_en = size_str.split("/")[0].strip().lower()
        
        if "small" in size_en:
            card_size = CardSize.SMALL
        elif "large" in size_en:
            card_size = CardSize.LARGE
        else:
            card_size = CardSize.MEDIUM
        
        # 计算尺寸 - 使用缩小的比例
        base_height = 50  # 缩小尺寸
        if card_size == CardSize.SMALL:
            img_w = int(base_height * 0.5)
        elif card_size == CardSize.LARGE:
            img_w = int(base_height * 1.5)
        else:
            img_w = base_height
        
        img_h = base_height
        
        # 创建容器 - 1px 半透明白色边框
        container = QLabel()
        container.setFixedSize(img_w + 2, img_h + 2)
        container.setStyleSheet("""
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 3px;
            background: #000;
        """)
        
        # 加载图片
        pix = ImageLoader.load_card_image(item_id, card_size, height=img_h, with_border=False)
        if not pix.isNull():
            scaled = pix.scaled(img_w, img_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            container.setPixmap(scaled)
            container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 添加 Tooltip 显示物品名称
        item_name = item_data.get("name", "")
        if "/" in item_name:
            item_name = item_name.split("/")[-1].strip()
        container.setToolTip(item_name)
        
        return container
    
    def _setup_animations(self):
        """设置动画"""
        # 展开动画
        self.expand_animation = QPropertyAnimation(self.details_widget, b"maximumHeight")
        self.expand_animation.setDuration(250)  # 缩短时间，更加干练
        
        # 动画结束时解锁
        self.expand_animation.finished.connect(self._on_animation_finished)
        
    def _toggle_expand(self):
        """切换展开/收起状态"""
        # 防止动画执行期间重复点击
        if self.is_animating:
            return
        
        if self.is_expanded:
            self._collapse()
        else:
            self._expand()
    
    def _on_animation_finished(self):
        """动画结束回调"""
        self.is_animating = False
        # 如果是收起状态，隐藏详情widget并重置高度
        if not self.is_expanded:
            self.details_widget.setVisible(False)
            self.details_widget.setMaximumHeight(0)
            self.details_widget.setMinimumHeight(0)
    
    def _expand(self):
        """展开详情"""
        self.is_animating = True
        self.is_expanded = True
        
        # 先设置可见并计算高度
        self.details_widget.setVisible(True)
        self.details_widget.setMaximumHeight(16777215)
        self.details_widget.setMinimumHeight(0)
        
        # 强制更新布局以获取正确的高度
        self.details_widget.adjustSize()
        target_height = self.details_widget.sizeHint().height()
        
        # 设置展开动画的缓动曲线
        self.expand_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # 动画展开
        self.expand_animation.setStartValue(0)
        self.expand_animation.setEndValue(target_height)
        self.expand_animation.start()
        
        # 箭头朝上
        self.expand_arrow.setText("∧")
        
    def _collapse(self):
        """收起详情"""
        self.is_animating = True
        self.is_expanded = False
        
        # 设置收起动画的缓动曲线（快速开始，平滑结束）
        self.expand_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        # 获取当前实际高度
        current_height = self.details_widget.height()
        
        # 动画收起
        self.expand_animation.setStartValue(current_height)
        self.expand_animation.setEndValue(0)
        self.expand_animation.start()
        
        # 箭头朝下
        self.expand_arrow.setText("∨")
    
    def enterEvent(self, event):
        """鼠标悬浮 - Hover 态"""
        # 侧边色条亮度加倍，背景色渐变
        self.setStyleSheet(f"""
            MatchCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #25211E,
                    stop:1 #1A1714);
                border: 1px solid rgba(212, 175, 55, 0.3);
                border-left: 4px solid {self.border_color};
                border-radius: 6px;
                margin-bottom: 8px;
            }}
        """)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开 - 恢复原样"""
        self.setStyleSheet(f"""
            MatchCard {{
                background-color: #1A1714;
                border: 1px solid rgba(212, 175, 55, 0.1);
                border-left: 4px solid {self.border_color};
                border-radius: 6px;
                margin-bottom: 8px;
            }}
        """)
        super().leaveEvent(event)


class LoadMatchesThread(QThread):
    """加载对局数据的后台线程"""
    finished_signal = Signal(list)  # 完成信号，传递sessions列表
    error_signal = Signal(str)  # 错误信号，传递错误信息
    
    def __init__(self, log_analyzer, items_db):
        super().__init__()
        self.log_analyzer = log_analyzer
        self.items_db = items_db
    
    def run(self):
        """在后台线程中执行"""
        try:
            result = self.log_analyzer.analyze()
            sessions = result.get("sessions", [])
            self.finished_signal.emit(sessions)
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
            self.error_signal.emit(error_msg)


class HistoryPageHolographic(QWidget):
    """历史战绩页面 - 全息卡片流设计"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化日志分析器
        from services.log_analyzer import get_log_directory
        log_dir = get_log_directory()
        
        # 传入 items_db 路径
        items_db_path = Path(__file__).parent.parent.parent / "assets" / "json" / "items_db.json"
        self.log_analyzer = LogAnalyzer(log_dir, str(items_db_path))
        
        # 加载物品数据库
        self.items_db = self._load_items_db()
        
        # ✅ 筛选状态
        self.selected_hero = None  # None = 显示所有英雄
        
        # ✅ 所有会话数据（缓存）
        self.all_sessions = []
        self.ongoing_session = None  # 正在进行的对局
        
        self._init_ui()
        
        # 创建加载线程
        self.load_thread = None
        
        # 异步加载数据，不阻塞UI打开
        self._show_loading_message()
        QTimer.singleShot(100, self._load_matches_async)
    
    def _load_items_db(self) -> dict:
        """加载物品数据库"""
        items_db_path = Path(__file__).parent.parent.parent / "assets" / "json" / "items_db.json"
        
        try:
            with open(items_db_path, 'r', encoding='utf-8') as f:
                items_list = json.load(f)
            
            items_dict = {}
            for item in items_list:
                item_id = item.get('id')
                if item_id:
                    items_dict[item_id] = item
            
            return items_dict
        except Exception as e:
            print(f"加载物品数据库失败: {e}")
            return {}
    
    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 标题栏
        header = self._create_header()
        main_layout.addWidget(header)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)  # 始终显示滚动条，避免展开时宽度变化
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: rgba(0, 0, 0, 0.3);
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: rgba(212, 175, 55, 0.3);
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(212, 175, 55, 0.5);
            }
        """)
        
        # 对局列表容器
        self.matches_container = QWidget()
        self.matches_layout = QVBoxLayout(self.matches_container)
        self.matches_layout.setContentsMargins(0, 0, 0, 0)
        self.matches_layout.setSpacing(8)  # 卡片间距 8px
        
        scroll_area.setWidget(self.matches_container)
        main_layout.addWidget(scroll_area)
        
        # 页面样式 - 最深黑背景
        self.setStyleSheet("""
            HistoryPageHolographic {
                background-color: #0F0E0D;
            }
        """)
    
    def _create_header(self) -> QWidget:
        """创建标题栏 - 极简风格 + 英雄筛选 + 排序切换"""
        header_container = QWidget()
        header_main_layout = QVBoxLayout(header_container)
        header_main_layout.setContentsMargins(0, 0, 0, 0)
        header_main_layout.setSpacing(12)
        
        # 第一行：标题 + 控制按钮
        first_row = QWidget()
        header_layout = QHBoxLayout(first_row)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(15)
        
        # 标题 - 金色
        title_label = QLabel("历史战绩")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 26px;
                font-weight: bold;
                color: #D4AF37;
                letter-spacing: 2px;
            }}
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 清除缓存按钮 - 极简样式
        clear_cache_btn = QPushButton("清除缓存")
        clear_cache_btn.setFixedHeight(36)
        clear_cache_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        clear_cache_btn.clicked.connect(self._clear_cache)
        clear_cache_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(245, 80, 61, 0.2);
                color: #F5503D;
                border: 1px solid rgba(245, 80, 61, 0.3);
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(245, 80, 61, 0.3);
                border-color: #F5503D;
            }
        """)
        header_layout.addWidget(clear_cache_btn)
        
        # 刷新按钮 - 金色主题
        refresh_btn = QPushButton("刷新")
        refresh_btn.setFixedHeight(36)
        refresh_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        refresh_btn.clicked.connect(self.refresh)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(212, 175, 55, 0.2);
                color: #D4AF37;
                border: 1px solid rgba(212, 175, 55, 0.3);
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(212, 175, 55, 0.3);
                border-color: #D4AF37;
            }
        """)
        header_layout.addWidget(refresh_btn)
        
        header_main_layout.addWidget(first_row)
        
        # ✅ 第二行：英雄筛选按钮
        second_row = QWidget()
        hero_filter_layout = QHBoxLayout(second_row)
        hero_filter_layout.setContentsMargins(0, 0, 0, 0)
        hero_filter_layout.setSpacing(12)
        
        # 筛选标签
        filter_label = QLabel("筛选英雄:")
        filter_label.setStyleSheet("""
            QLabel {
                color: #999;
                font-size: 13px;
            }
        """)
        hero_filter_layout.addWidget(filter_label)
        
        # 6个英雄头像按钮
        self.hero_buttons = {}
        heroes = ["Vanessa", "Pygmalien", "Dooley", "Jules", "Mak", "Stelle"]
        
        for hero_name in heroes:
            hero_btn = QPushButton()
            hero_btn.setFixedSize(42, 42)
            hero_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            hero_btn.setCheckable(True)
            
            # 加载英雄头像
            hero_image_path = Path(__file__).parent.parent.parent / "assets" / "images" / "heroes" / f"{hero_name.lower()}.webp"
            
            if hero_image_path.exists():
                pixmap = QPixmap(str(hero_image_path))
                if not pixmap.isNull():
                    # 创建圆形图标
                    icon = QIcon(pixmap)
                    hero_btn.setIcon(icon)
                    hero_btn.setIconSize(QSize(38, 38))
            else:
                hero_btn.setText(hero_name[0])
            
            # 设置样式
            hero_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.05);
                    border: 2px solid rgba(255, 255, 255, 0.1);
                    border-radius: 21px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                    border-color: rgba(212, 175, 55, 0.5);
                }
                QPushButton:checked {
                    background-color: rgba(212, 175, 55, 0.2);
                    border: 2px solid #D4AF37;
                }
            """)
            
            hero_btn.clicked.connect(lambda checked, h=hero_name: self._on_hero_filter_clicked(h))
            hero_filter_layout.addWidget(hero_btn)
            self.hero_buttons[hero_name] = hero_btn
        
        # "全部"按钮
        all_btn = QPushButton("全部")
        all_btn.setFixedSize(42, 42)
        all_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        all_btn.setCheckable(True)
        all_btn.setChecked(True)  # 默认选中
        all_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.05);
                border: 2px solid rgba(255, 255, 255, 0.1);
                border-radius: 21px;
                font-size: 11px;
                color: #999;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-color: rgba(212, 175, 55, 0.5);
                color: #D4AF37;
            }
            QPushButton:checked {
                background-color: rgba(212, 175, 55, 0.2);
                border: 2px solid #D4AF37;
                color: #D4AF37;
                font-weight: bold;
            }
        """)
        all_btn.clicked.connect(lambda: self._on_hero_filter_clicked(None))
        hero_filter_layout.addWidget(all_btn)
        self.hero_buttons["All"] = all_btn
        
        hero_filter_layout.addStretch()
        
        header_main_layout.addWidget(second_row)
        
        return header_container
    
    def _clear_cache(self):
        """清除缓存"""
        try:
            cache_file = Path(__file__).parent.parent.parent / "user_data" / "game_sessions_cache.json"
            if cache_file.exists():
                cache_file.unlink()
                print("缓存已清除")
            
            # 重新加载
            self.refresh()
        except Exception as e:
            print(f"清除缓存失败: {e}")
    
    def _show_loading_message(self):
        """显示加载中提示（带进度条）"""
        while self.matches_layout.count():
            item = self.matches_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 创建加载容器
        loading_container = QWidget()
        loading_layout = QVBoxLayout(loading_container)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_layout.setSpacing(20)
        
        loading_label = QLabel("正在分析游戏日志...")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #D4AF37;
                letter-spacing: 1px;
            }
        """)
        loading_layout.addWidget(loading_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(400)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setRange(0, 0)  # 不确定进度，显示动画
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(212, 175, 55, 0.1);
                border: 1px solid rgba(212, 175, 55, 0.2);
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(212, 175, 55, 0.3),
                    stop:0.5 rgba(212, 175, 55, 0.8),
                    stop:1 rgba(212, 175, 55, 0.3));
                border-radius: 3px;
            }
        """)
        loading_layout.addWidget(self.progress_bar, 0, Qt.AlignmentFlag.AlignCenter)
        
        loading_layout.addStretch()
        
        self.matches_layout.addWidget(loading_container)
    
    def _load_matches_async(self):
        """异步加载对局列表（在UI打开后执行，使用线程）"""
        if self.load_thread is not None and self.load_thread.isRunning():
            return
        
        # 创建并启动加载线程
        self.load_thread = LoadMatchesThread(self.log_analyzer, self.items_db)
        self.load_thread.finished_signal.connect(self._on_load_finished)
        self.load_thread.error_signal.connect(self._on_load_error)
        self.load_thread.start()
    
    def _on_load_finished(self, sessions):
        """加载完成回调"""
        # ✅ 分离正在进行和已完成的对局
        if sessions:
            # 正在进行的对局：最后一个且未完成
            last_session = sessions[-1]
            if not last_session.is_finished:
                self.ongoing_session = last_session
                self.all_sessions = sessions[:-1]  # 已完成的对局
            else:
                self.ongoing_session = None
                self.all_sessions = sessions
        else:
            self.ongoing_session = None
            self.all_sessions = []
        
        # 更新显示
        self._update_display()
    
    def _update_display(self):
        """更新显示（应用筛选）"""
        # 清空现有显示
        while self.matches_layout.count():
            item = self.matches_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # ✅ 1. 显示正在进行的对局（如果有）
        if self.ongoing_session:
            # 检查英雄筛选
            if not self.selected_hero or getattr(self.ongoing_session, 'hero', None) == self.selected_hero:
                # 正在进行标签 - 显示天数和战绩
                battles = self.ongoing_session.pvp_battles
                wins = sum(1 for b in battles if b.get('victory', False))
                losses = len(battles) - wins
                ongoing_label = QLabel(f"🔴 正在进行 - 第{self.ongoing_session.days}天 ({wins}胜{losses}负)")
                ongoing_label.setStyleSheet("""
                    QLabel {
                        color: #00ECC3;
                        font-size: 13px;
                        font-weight: bold;
                        padding: 8px 0;
                        letter-spacing: 1px;
                    }
                """)
                self.matches_layout.addWidget(ongoing_label)
                
                # 正在进行的对局卡片
                ongoing_card = MatchCard(self.ongoing_session, 0, self.items_db)
                self.matches_layout.addWidget(ongoing_card)
                
                # 分隔线
                separator = QFrame()
                separator.setFrameShape(QFrame.Shape.HLine)
                separator.setStyleSheet("background-color: rgba(255, 255, 255, 0.1); max-height: 2px; margin: 12px 0;")
                self.matches_layout.addWidget(separator)
        
        # ✅ 2. 筛选已完成的会话
        filtered_sessions = self.all_sessions
        if self.selected_hero:
            filtered_sessions = [s for s in self.all_sessions if getattr(s, 'hero', None) == self.selected_hero]
        
        # ✅ 3. 按日志中的自然顺序显示（不排序）
        # 最早出现在日志中的在列表前面，但显示时从后往前（最近的在上面）
        display_sessions = list(reversed(filtered_sessions))
        
        if not display_sessions and not self.ongoing_session:
            empty_label = QLabel("暂无符合条件的战绩记录")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("""
                QLabel {
                    font-size: 15px;
                    color: #666;
                    padding: 80px;
                    line-height: 1.6;
                }
            """)
            self.matches_layout.addWidget(empty_label)
        else:
            # 创建对局卡片
            for idx, session in enumerate(display_sessions, 1):
                match_card = MatchCard(session, idx, self.items_db)
                self.matches_layout.addWidget(match_card)
        
        self.matches_layout.addStretch()
    
    def _on_hero_filter_clicked(self, hero_name: str = None):
        """英雄筛选按钮点击"""
        self.selected_hero = hero_name
        
        # 更新按钮选中状态
        for h, btn in self.hero_buttons.items():
            if h == "All" and hero_name is None:
                btn.setChecked(True)
            elif h == hero_name:
                btn.setChecked(True)
            else:
                btn.setChecked(False)
        
        # 重新显示
        self._update_display()
    
    def _on_load_error(self, error_msg):
        """加载错误回调"""
        while self.matches_layout.count():
            item = self.matches_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        error_label = QLabel(f"加载失败\n\n{error_msg}")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("""
            QLabel {
                font-size: 15px;
                color: #F5503D;
                padding: 80px;
                line-height: 1.6;
            }
        """)
        self.matches_layout.addWidget(error_label)
        self.matches_layout.addStretch()
    
    def refresh(self):
        """刷新页面"""
        self._show_loading_message()
        QTimer.singleShot(50, self._load_matches_async)
