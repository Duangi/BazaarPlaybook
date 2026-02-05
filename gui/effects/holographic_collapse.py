# gui/effects/holographic_collapse.py
"""全息收缩动效：将一个窗口“压扁成金线”，并飞向目标胶囊。

实现思路（轻量、稳定）：
- 基于 QPropertyAnimation 动画窗口 geometry
- 叠加一个透明的 Overlay 窗口（跟随源窗口），绘制：
  - 中央扫描线（收缩为一条金线）
  - 金色粒子方块（可选，数量不大以保证性能）
- 动画结束：隐藏源窗口，显示目标窗口

注：Qt 对窗口 mask 在 Win 上配合半透明时容易出现锯齿/闪烁，
这里优先使用 overlay 绘制视觉效果，观感更“电竞”，也更稳。
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from PySide6.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve, QTimer, QPointF
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import QWidget


@dataclass
class _Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    size: float


class HoloCollapseOverlay(QWidget):
    """覆盖层：绘制扫描线 + 粒子。"""

    def __init__(self, source_rect: QRect, *, enable_particles: bool = True):
        super().__init__(None)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.setGeometry(source_rect)

        self.progress = 0.0  # 0..1
        self.enable_particles = enable_particles

        self._particles: list[_Particle] = []
        if self.enable_particles:
            self._spawn_particles()

        self._tick = QTimer(self)
        self._tick.setInterval(16)
        self._tick.timeout.connect(self._update_particles)
        self._tick.start()

    def set_progress(self, p: float):
        self.progress = max(0.0, min(1.0, p))
        self.update()

    def _spawn_particles(self):
        w = max(1, self.width())
        h = max(1, self.height())
        count = min(180, max(60, (w * h) // 6000))
        for _ in range(count):
            x = random.uniform(0, w)
            y = random.uniform(0, h)
            # 向中心收束
            cx, cy = w / 2, h / 2
            dx, dy = (cx - x), (cy - y)
            k = random.uniform(0.002, 0.006)
            vx, vy = dx * k, dy * k
            self._particles.append(
                _Particle(x=x, y=y, vx=vx, vy=vy, life=random.uniform(0.6, 1.0), size=random.uniform(1.2, 2.6))
            )

    def _update_particles(self):
        if not self.enable_particles:
            return
        # 进度越大越“吸入”
        absorb = 0.6 + self.progress * 1.8
        for p in self._particles:
            p.x += p.vx * absorb
            p.y += p.vy * absorb
            p.life -= 0.012 * absorb
        self._particles = [p for p in self._particles if p.life > 0]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        if w <= 0 or h <= 0:
            return

        # 扫描线：由“窗口厚度”收缩到 2px，再变点
        # thickness: h -> 2
        thickness = max(2.0, h * (1.0 - self.progress) ** 2)
        alpha = int(220 * (1.0 - self.progress * 0.85))

        # 中央金线
        y = h / 2 - thickness / 2
        line_rect = QRect(10, int(y), max(1, w - 20), int(thickness))

        # 外发光
        glow_pen = QPen(QColor(255, 204, 0, min(140, alpha)))
        glow_pen.setWidth(2)
        painter.setPen(glow_pen)
        painter.setBrush(QColor(255, 204, 0, min(40, alpha)))
        painter.drawRoundedRect(line_rect, 8, 8)

        # 内核更亮
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 204, 0, min(220, alpha)))
        core = line_rect.adjusted(0, max(0, int(thickness * 0.25)), 0, -max(0, int(thickness * 0.25)))
        painter.drawRoundedRect(core, 8, 8)

        # 粒子（方块解构）
        if self.enable_particles and self._particles:
            painter.setPen(Qt.NoPen)
            for p in self._particles:
                a = int(180 * max(0.0, min(1.0, p.life)))
                painter.setBrush(QColor(255, 204, 0, a))
                painter.drawRect(int(p.x), int(p.y), int(p.size), int(p.size))


class HolographicCollapse:
    """对外 API：把 source_window 全息收缩到 target_rect，并在结束时触发回调。"""

    def __init__(
        self,
        source_window: QWidget,
        target_rect: QRect,
        *,
        duration: int = 540,
        enable_particles: bool = True,
    ):
        self.source_window = source_window
        self.target_rect = target_rect
        self.duration = duration
        self.enable_particles = enable_particles

        self.overlay: HoloCollapseOverlay | None = None
        self.anim: QPropertyAnimation | None = None
        self._on_finished = None

    def start(self, on_finished=None):
        self._on_finished = on_finished

        start_rect = self.source_window.geometry()

        self.overlay = HoloCollapseOverlay(start_rect, enable_particles=self.enable_particles)
        self.overlay.show()

        # 几何动画：收缩到目标胶囊
        self.anim = QPropertyAnimation(self.source_window, b"geometry")
        self.anim.setDuration(self.duration)
        self.anim.setStartValue(start_rect)
        self.anim.setEndValue(self.target_rect)
        self.anim.setEasingCurve(QEasingCurve.InOutCubic)

        # 同步进度
        self.anim.valueChanged.connect(self._on_value_changed)
        self.anim.finished.connect(self._finish)
        self.anim.start()

    def _on_value_changed(self, value):
        if not self.overlay:
            return
        rect: QRect = value
        # overlay 跟随窗口
        self.overlay.setGeometry(rect)
        # progress：按面积收缩近似
        start_area = max(1, self.source_window.width() * self.source_window.height())
        area = max(1, rect.width() * rect.height())
        p = 1.0 - min(1.0, area / start_area)
        self.overlay.set_progress(p)

    def _finish(self):
        if self.overlay:
            self.overlay.hide()
            self.overlay.deleteLater()
            self.overlay = None
        if self._on_finished:
            self._on_finished()
