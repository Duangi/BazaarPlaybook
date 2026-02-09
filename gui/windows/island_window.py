# gui/windows/island_window.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal, QPoint, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QLinearGradient

class IslandWindow(QWidget):
    """灵动岛 - 核心态势感知中心"""
    
    expand_requested = Signal()  # 请求展开侧边栏
    
    # 岛的状态
    STATE_NORMAL = "normal"      # 常态：信息胶囊
    STATE_SCANNING = "scanning"  # 识别态：流光扫描
    STATE_CONFIRM = "confirm"    # 确权态：确认反馈
    STATE_ALERT = "alert"        # 警报态：机械展开
    
    def __init__(self):
        super().__init__()
        
        # 窗口设置
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool  # 不在任务栏显示
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)  # 初始不穿透
        
        # 状态
        self.current_state = self.STATE_NORMAL
        self._drag_pos = QPoint()
        self._is_dragging = False
        self._hover_timer = None
        
        # 尺寸定义
        self.normal_width = 200
        self.normal_height = 36
        self.expanded_height = 60
        
        # 设置初始大小和位置（屏幕顶部中央）
        self.resize(self.normal_width, self.normal_height)
        self._move_to_top_center()
        
        # UI
        self._setup_ui()
        
        # 动画
        self._setup_animations()
        
    def set_scanner_status(self, is_active: bool, message: str = ""):
        """设置扫描器状态"""
        if is_active:
            self.lbl_day.setText("Auto Scan: ON")
            self.lbl_day.setStyleSheet("color: #00ff00; font-weight: bold;") # Green
        else:
            self.lbl_day.setText("Auto Scan: OFF")
            self.lbl_day.setStyleSheet("color: #888888;")
            
        if message:
             self.lbl_phase.setText(message)

    def _setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 8, 15, 8)
        layout.setSpacing(10)
        
        # 日期标签
        self.lbl_day = QLabel("Day 13")
        self.lbl_day.setObjectName("IslandDay")
        self.lbl_day.setStyleSheet("""
            QLabel#IslandDay {
                color: #ffcc00;
                font-size: 13px;
                font-weight: bold;
                font-family: 'Microsoft YaHei UI', 'Segoe UI';
            }
        """)
        layout.addWidget(self.lbl_day)
        
        # 分隔符
        separator = QLabel("•")
        separator.setStyleSheet("""
            QLabel {
                color: rgba(255, 204, 0, 0.5);
                font-size: 10px;
            }
        """)
        layout.addWidget(separator)
        
        # 状态标签
        self.lbl_phase = QLabel("Phase: Shop")
        self.lbl_phase.setObjectName("IslandPhase")
        self.lbl_phase.setStyleSheet("""
            QLabel#IslandPhase {
                color: rgba(255, 204, 0, 0.8);
                font-size: 12px;
                font-family: 'Microsoft YaHei UI', 'Segoe UI';
            }
        """)
        layout.addWidget(self.lbl_phase)
        
        layout.addStretch()
        
    def _setup_animations(self):
        """设置动画"""
        # 高度动画（用于展开/收起效果）
        self.height_anim = QPropertyAnimation(self, b"geometry")
        self.height_anim.setDuration(300)
        self.height_anim.setEasingCurve(QEasingCurve.OutCubic)
        
    def _move_to_top_center(self):
        """移动到屏幕顶部中央"""
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = 10  # 距离顶部10px
        self.move(x, y)
        
    def paintEvent(self, event):
        """自定义绘制 - 实现流光效果"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        
        # 背景（黑色半透明）
        painter.setBrush(QColor(20, 20, 25, 220))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 18, 18)
        
        # 边框（根据状态变化）
        if self.current_state == self.STATE_NORMAL:
            # 常态：暗金色细边框
            pen = QPen(QColor(255, 204, 0, 100))
            pen.setWidth(1)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 18, 18)
            
        elif self.current_state == self.STATE_SCANNING:
            # 识别态：流光边框（渐变）
            gradient = QLinearGradient(0, 0, rect.width(), 0)
            gradient.setColorAt(0.0, QColor(255, 204, 0, 50))
            gradient.setColorAt(0.5, QColor(255, 204, 0, 255))
            gradient.setColorAt(1.0, QColor(255, 204, 0, 50))
            
            pen = QPen(gradient, 2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 18, 18)
            
        elif self.current_state == self.STATE_CONFIRM:
            # 确权态：亮金色边框
            pen = QPen(QColor(255, 204, 0, 255))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 18, 18)
            
    def set_state(self, state):
        """设置岛的状态"""
        self.current_state = state
        self.update()  # 触发重绘
        
    def set_day(self, day):
        """设置天数"""
        self.lbl_day.setText(f"Day {day}")
        
    def set_phase(self, phase):
        """设置阶段"""
        self.lbl_phase.setText(f"Phase: {phase}")
        
    def mousePressEvent(self, event):
        """鼠标按下 - 开始拖动"""
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            self._drag_pos = event.globalPosition().toPoint() - self.pos()
            
    def mouseMoveEvent(self, event):
        """鼠标移动 - 拖动窗口"""
        if self._is_dragging and event.buttons() == Qt.LeftButton:
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            self.move(new_pos)
            
    def mouseReleaseEvent(self, event):
        """鼠标释放 - 磁吸效果"""
        if event.button() == Qt.LeftButton:
            self._is_dragging = False
            # 检查是否靠近屏幕顶部中央，如果是则吸附
            self._magnetic_snap()
            
    def mouseDoubleClickEvent(self, event):
        """双击 - 展开侧边栏"""
        if event.button() == Qt.LeftButton:
            self.expand_requested.emit()
            
    def show_detection_feedback(self, text: str):
        """Show detection feedback (Flash green + Text)"""
        if not text: return
        
        # Format Text
        self.lbl_phase.setText(f"Found: {text}")
        
        # Flash Green Style
        self.lbl_phase.setStyleSheet("""
            QLabel#IslandPhase {
                color: #00ff00;
                font-size: 13px;
                font-weight: bold;
                font-family: 'Microsoft YaHei UI', 'Segoe UI';
            }
        """)
        
        # Flash Animation (Opacity pulse)
        if not hasattr(self, '_flash_anim'):
            self._flash_anim = QPropertyAnimation(self, b"windowOpacity")
            self._flash_anim.setDuration(150)
            self._flash_anim.setLoopCount(2)
            self._flash_anim.setKeyValueAt(0, 1.0)
            self._flash_anim.setKeyValueAt(0.5, 0.7)
            self._flash_anim.setKeyValueAt(1, 1.0)
        
        self._flash_anim.start()

        # Auto Restore
        if hasattr(self, '_restore_timer'):
             self._restore_timer.stop()
        
        from PySide6.QtCore import QTimer
        self._restore_timer = QTimer(self)
        self._restore_timer.setSingleShot(True)
        self._restore_timer.timeout.connect(self._restore_phase_text)
        self._restore_timer.start(2000)

    def _restore_phase_text(self):
        if hasattr(self, 'lbl_phase'):
            self.lbl_phase.setText("Phase: Shop")
            self.lbl_phase.setStyleSheet("""
                QLabel#IslandPhase {
                    color: rgba(255, 204, 0, 0.8);
                    font-size: 12px;
                    font-family: 'Microsoft YaHei UI', 'Segoe UI';
                }
            """)

    def _magnetic_snap(self):
        """磁吸到屏幕顶部中央"""
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        
        # 计算理想位置（顶部中央）
        ideal_x = (screen.width() - self.width()) // 2
        ideal_y = 10
        
        # 如果当前位置在顶部区域（y < 100）且靠近中央（x 在屏幕中央 ±200px 范围内）
        current_pos = self.pos()
        if current_pos.y() < 100 and abs(current_pos.x() - ideal_x) < 200:
            # 平滑移动到理想位置
            anim = QPropertyAnimation(self, b"pos")
            anim.setDuration(200)
            anim.setStartValue(current_pos)
            anim.setEndValue(QPoint(ideal_x, ideal_y))
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.start()
            
            # 保存动画引用，防止被垃圾回收
            self._snap_anim = anim
