#!/usr/bin/env python3
"""
Mikrofon — Pływająca ikona stanu mikrofonu dla Linux/X11
────────────────────────────────────────────────────────
  🟢 zielona = mikrofon aktywny
  🔴 czerwona = mikrofon wyciszony

Obsługa:
  • przeciągnij lewym przyciskiem  — przesuń ikonę
  • podwójny klik lewym            — wycisz / odcisz mikrofon
  • prawy przycisk                 — menu kontekstowe
"""
import sys
import subprocess

from PyQt6.QtWidgets import QApplication, QWidget, QMenu
from PyQt6.QtCore import Qt, QTimer, QProcess, QRectF, QPointF, QPoint
from PyQt6.QtGui import (
    QPainter, QColor, QBrush, QPen,
    QRadialGradient, QPainterPath,
)

SIZE = 120  # rozmiar widgetu [px]


# ── audio ─────────────────────────────────────────────────────────────────

def get_mute_state() -> bool | None:
    """True = wyciszony, False = aktywny, None = błąd."""
    try:
        r = subprocess.run(
            ["pactl", "get-source-mute", "@DEFAULT_SOURCE@"],
            capture_output=True, text=True, timeout=1,
        )
        return "yes" in r.stdout.lower()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None


def toggle_mute() -> None:
    subprocess.run(
        ["pactl", "set-source-mute", "@DEFAULT_SOURCE@", "toggle"],
        capture_output=True,
        timeout=2,
    )


# ── widget ────────────────────────────────────────────────────────────────

class MikrofonWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.muted: bool = False
        self._drag_pos: QPoint | None = None
        self._flash: int = 0          # klatki animacji zmiany stanu

        # timer tylko do odliczania klatek rozbłysku (nie do pollingu)
        self._flash_timer = QTimer(self)
        self._flash_timer.setInterval(80)
        self._flash_timer.timeout.connect(self._tick_flash)

        self._setup_window()
        self._place_on_screen()
        self._setup_subscriber()
        self._refresh_state()   # jednorazowy odczyt stanu na starcie

    # ── konfiguracja okna ────────────────────────────────────────────────

    def _setup_window(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setFixedSize(SIZE, SIZE)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setToolTip("Mikrofon — podwójny klik: wycisz/odcisz\nprawy przycisk: menu")

    def _place_on_screen(self) -> None:
        geo = QApplication.primaryScreen().availableGeometry()
        self.move(geo.right() - SIZE - 20, geo.bottom() - SIZE - 48)

    # ── subskrypcja zdarzeń audio ────────────────────────────────────────

    def _setup_subscriber(self) -> None:
        """Uruchamia `pactl subscribe` i słucha zdarzeń zmiany źródła."""
        if hasattr(self, "_proc"):
            self._proc.finished.disconnect()
            self._proc.deleteLater()
        self._proc = QProcess(self)
        self._proc.readyReadStandardOutput.connect(self._on_pactl_event)
        self._proc.finished.connect(self._on_subscriber_died)
        self._proc.start("pactl", ["subscribe"])

    def _on_pactl_event(self) -> None:
        """Wywoływany gdy pactl subscribe wyemituje nową linię."""
        while self._proc.canReadLine():
            line = bytes(self._proc.readLine()).decode("utf-8", errors="ignore").strip()
            # Linie wyglądają np.: "Event 'change' on source #61"
            if "source" in line:
                self._refresh_state()

    def _on_subscriber_died(self) -> None:
        """Jeśli pactl padnie — restart po 1 s."""
        QTimer.singleShot(1000, self._setup_subscriber)

    def _refresh_state(self) -> None:
        """Jednorazowy odczyt aktualnego stanu wyciszenia przez pactl."""
        state = get_mute_state()
        if state is None:
            return
        if state != self.muted:
            self.muted = state
            self._flash = 6         # uruchom animację rozbłysku
            self._flash_timer.start()
            self.update()

    def _tick_flash(self) -> None:
        """Odlicza klatki rozbłysku; zatrzymuje timer gdy skończy."""
        if self._flash > 0:
            self._flash -= 1
            self.update()
        else:
            self._flash_timer.stop()

    # ── rysowanie ────────────────────────────────────────────────────────

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = float(self.width()), float(self.height())
        cx, cy = w / 2, h / 2
        r = min(w, h) / 2 - 3

        # --- cień ---
        for i in range(5, 0, -1):
            p.setBrush(QBrush(QColor(0, 0, 0, 16 * (6 - i))))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(
                QRectF(cx - r + i * 0.35, cy - r + i * 0.75, r * 2, r * 2)
            )

        # --- tło: gradient radialny ---
        flash_boost = 30 if self._flash > 0 else 0
        grad = QRadialGradient(cx - r * 0.2, cy - r * 0.3, r * 1.3)
        if self.muted:
            grad.setColorAt(0.0, QColor(255, 110 + flash_boost, 90))
            grad.setColorAt(1.0, QColor(185, 30, 30))
        else:
            grad.setColorAt(0.0, QColor(90, 225 + flash_boost, 130))
            grad.setColorAt(1.0, QColor(25, 155, 65))

        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        # --- połysk ---
        shine = QRadialGradient(cx - r * 0.15, cy - r * 0.55, r * 0.72)
        shine.setColorAt(0.0, QColor(255, 255, 255, 65))
        shine.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(QBrush(shine))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        # --- ikona mikrofonu ---
        self._draw_mic(p, cx, cy, r)

        # --- przekreślenie gdy wyciszony ---
        if self.muted:
            slash = QPen(QColor(255, 255, 255, 215), max(2.2, r * 0.095))
            slash.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(slash)
            m = r * 0.28
            p.drawLine(
                QPointF(cx - r + m, cy - r + m),
                QPointF(cx + r - m, cy + r - m),
            )

    def _draw_mic(self, p: QPainter, cx: float, cy: float, r: float) -> None:
        s = r / 25.0          # skala względem promienia

        # kapsuła (zaokrąglony prostokąt)
        mw = 10 * s           # szerokość kapsuły
        mh = 18 * s           # wysokość kapsuły
        mx = cx - mw / 2
        my = cy - mh * 0.62   # nieco powyżej środka

        path = QPainterPath()
        path.addRoundedRect(QRectF(mx, my, mw, mh), mw / 2, mw / 2)
        p.setBrush(QBrush(QColor(255, 255, 255, 215)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(path)

        # łuk (U-kształt pod kapsuł)
        pen = QPen(QColor(255, 255, 255, 215), max(1.5, 1.8 * s))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        arc_r = 8 * s
        arc_cy = my + mh                            # dół kapsułki = środek łuku
        arc_rect = QRectF(cx - arc_r, arc_cy - arc_r, arc_r * 2, arc_r * 2)
        p.drawArc(arc_rect, 180 * 16, -180 * 16)   # U-kształt w dół

        # słupek
        stand_top = arc_cy + arc_r
        stand_bot = cy + r * 0.60
        p.drawLine(QPointF(cx, stand_top), QPointF(cx, stand_bot))

        # podstawka
        bw = 8 * s
        p.drawLine(QPointF(cx - bw, stand_bot), QPointF(cx + bw, stand_bot))

    # ── zdarzenia myszy ───────────────────────────────────────────────────

    def mousePressEvent(self, ev) -> None:  # noqa: N802
        if ev.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (
                ev.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        elif ev.button() == Qt.MouseButton.RightButton:
            self._show_menu(ev.globalPosition().toPoint())

    def mouseMoveEvent(self, ev) -> None:  # noqa: N802
        if self._drag_pos and (ev.buttons() & Qt.MouseButton.LeftButton):
            self.move(ev.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, ev) -> None:  # noqa: N802
        self._drag_pos = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def mouseDoubleClickEvent(self, ev) -> None:  # noqa: N802
        if ev.button() == Qt.MouseButton.LeftButton:
            toggle_mute()
            # pactl subscribe wyemituje event sam — nie potrzeba ręcznego odczytu

    # ── menu kontekstowe ──────────────────────────────────────────────────

    def _show_menu(self, pos) -> None:
        menu = QMenu(self)
        state_txt = "🔴  Wyciszony" if self.muted else "🟢  Aktywny"
        menu.addAction(state_txt).setEnabled(False)
        menu.addSeparator()
        toggle_act = menu.addAction("Wycisz / Odcisz  (lub 2× klik)")
        menu.addSeparator()
        quit_act = menu.addAction("Zamknij")

        chosen = menu.exec(pos)
        if chosen == toggle_act:
            toggle_mute()
            # pactl subscribe wyemituje event sam
        elif chosen == quit_act:
            QApplication.quit()


# ── entry point ───────────────────────────────────────────────────────────

def main() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    widget = MikrofonWidget()
    widget.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
