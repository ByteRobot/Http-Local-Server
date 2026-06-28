"""
Nova Server — Professional PyQt5 GUI for a local HTTP file server.

Features:
  • Light green theme with crisp contrast & clear typography
  • Smooth button hover animations & sidebar slide
  • Status badge with pulsing indicator
  • QR code dialog
  • Log filtering (regex / plain)
  • Uptime, request & byte counters
  • Auto-port detection
  • Graceful stop with transfer abort
  • Settings persistence (QSettings)
  • Auto-start on launch option
  • Scrollable main panel so nothing ever overlaps, even on small screens

Dependencies:
    pip install PyQt5 qrcode pillow

Run:
    python nova_server.py
"""

import sys
import os
import socket
import time
import io
import re
from http.server import SimpleHTTPRequestHandler
from socketserver import ThreadingTCPServer
from functools import partial
from dataclasses import dataclass
from typing import Optional

from PyQt5.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, pyqtSlot, QPropertyAnimation,
    QEasingCurve, QObject, QSettings, pyqtProperty
)
from PyQt5.QtGui import (
    QFont, QColor, QPixmap, QPainter, QBrush, QPalette
)
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QLineEdit, QTextEdit, QComboBox, QSpinBox, QFrame,
    QScrollArea, QMessageBox, QGraphicsDropShadowEffect,
    QCheckBox, QSizePolicy, QDialog
)

try:
    import qrcode
    HAS_QR = True
except ImportError:
    HAS_QR = False

# ─────────────────────────────────────────────────────────────
# PALETTE (Light green, high-contrast, developer-tool aesthetic)
# ─────────────────────────────────────────────────────────────
C = {
    "bg":          "#F5FBF6",   # page background (very light green tint)
    "surface":     "#FFFFFF",   # card / panel background
    "surface2":    "#EAF7EE",   # secondary surface (sidebar)
    "border":      "#D7ECDD",   # borders
    "border_focus":"#2FB36C",   # focused input border

    "accent":      "#2FB36C",   # primary action (light green)
    "accent_dark": "#239456",   # hover (darker green)
    "accent_soft": "#E1F7E9",   # soft accent tint
    "accent_light":"#8FE3B0",   # gradient highlight

    "danger":      "#E84545",   # stop / error
    "danger_dark": "#C43030",
    "warn":        "#F59D00",   # warning
    "success":     "#1FA862",   # running indicator

    "text":        "#1A271F",   # primary text
    "text_sec":    "#5C7768",   # secondary / muted text
    "text_inv":    "#FFFFFF",   # on dark / accent backgrounds

    "log_bg":      "#102318",   # log panel (dark, for contrast with mono text)
    "log_text":    "#CFEFD9",
    "log_ts":      "#6FA084",
    "log_error":   "#FF6B6B",
    "log_info":    "#5EEAD4",
}


# ─────────────────────────────────────────────────────────────
# Network helpers
# ─────────────────────────────────────────────────────────────
def get_primary_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def find_free_port(start: int = 8000, end: int = 9000) -> Optional[int]:
    for p in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", p))
                return p
            except OSError:
                continue
    return None


def get_all_ips() -> list:
    ips = set()
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None):
            ip = info[4][0]
            if ":" not in ip:  # skip IPv6
                ips.add(ip)
    except Exception:
        pass
    ips.add(get_primary_ip())
    ips.add("127.0.0.1")
    return sorted(ips)


# ─────────────────────────────────────────────────────────────
# Stats & cross-thread signals
# ─────────────────────────────────────────────────────────────
@dataclass
class ServerStats:
    start_time: float = 0.0
    requests: int = 0
    bytes_sent: int = 0
    running: bool = False


class _Emitter(QObject):
    log_signal   = pyqtSignal(str, str)   # (message, level)  level: info|warn|error
    stats_signal = pyqtSignal(int, int)   # requests, bytes


stats_emitter = _Emitter()


# ─────────────────────────────────────────────────────────────
# HTTP request handler
# ─────────────────────────────────────────────────────────────
class LoggingHTTPRequestHandler(SimpleHTTPRequestHandler):
    server_version = "NovaServer/2.0"

    def log_message(self, fmt, *args):
        msg = "[%s] %s" % (self.log_date_time_string(), fmt % args)
        level = "error" if "4" in (args[1] if len(args) > 1 else "") or "5" in (args[1] if len(args) > 1 else "") else "info"
        stats_emitter.log_signal.emit(msg, level)

    def do_GET(self):
        if getattr(self.server, "should_stop", False):
            self.send_error(503, "Server stopping")
            return
        super().do_GET()
        self.server.stats.requests += 1
        stats_emitter.stats_signal.emit(
            self.server.stats.requests, self.server.stats.bytes_sent
        )

    def do_HEAD(self):
        if getattr(self.server, "should_stop", False):
            self.send_error(503, "Server stopping")
            return
        super().do_HEAD()

    def copyfile(self, source, outputfile):
        total = 0
        while not getattr(self.server, "should_stop", False):
            buf = source.read(64 * 1024)
            if not buf:
                break
            try:
                outputfile.write(buf)
            except (BrokenPipeError, ConnectionResetError):
                break
            total += len(buf)
        self.server.stats.bytes_sent += total
        stats_emitter.stats_signal.emit(
            self.server.stats.requests, self.server.stats.bytes_sent
        )

    def log_error(self, fmt, *args):
        msg = "[%s] ERROR: %s" % (self.log_date_time_string(), fmt % args)
        stats_emitter.log_signal.emit(msg, "error")


# ─────────────────────────────────────────────────────────────
# Server thread
# ─────────────────────────────────────────────────────────────
class HttpServerThread(QThread):
    started_signal = pyqtSignal()
    stopped_signal = pyqtSignal()
    error_signal   = pyqtSignal(str)

    def __init__(self, directory: str, host: str, port: int, parent=None):
        super().__init__(parent)
        self.directory = directory
        self.host = host
        self.port = port
        self.httpd = None
        self._stopping = False

    def run(self):
        try:
            handler = partial(LoggingHTTPRequestHandler, directory=self.directory)
            ThreadingTCPServer.allow_reuse_address = True
            self.httpd = ThreadingTCPServer((self.host, self.port), handler)
            self.httpd.stats = ServerStats(time.time(), 0, 0, True)
            self.httpd.should_stop = False
            self.started_signal.emit()
            self.httpd.serve_forever(poll_interval=0.15)
        except OSError as e:
            if not self._stopping:
                self.error_signal.emit(str(e))
        except Exception as e:
            if not self._stopping:
                self.error_signal.emit(repr(e))
        finally:
            if self.httpd:
                try:
                    self.httpd.server_close()
                except Exception:
                    pass
            self.stopped_signal.emit()

    def stop(self):
        self._stopping = True
        if self.httpd:
            self.httpd.should_stop = True
            try:
                self.httpd.shutdown()
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────
# Animated button
# ─────────────────────────────────────────────────────────────
class StyledButton(QPushButton):
    """Pill-shaped button with smooth color-fade on hover."""

    # variant: "primary" | "danger" | "ghost" | "outline" | "success"
    VARIANTS = {
        "primary": (C["accent"],      C["accent_dark"], C["text_inv"]),
        "danger":  (C["danger"],      C["danger_dark"], C["text_inv"]),
        "ghost":   (C["surface2"],    C["border"],      C["text"]),
        "outline": ("transparent",    C["accent_soft"], C["accent"]),
        "success": (C["success"],     "#168A50",        C["text_inv"]),
    }

    def __init__(self, text: str = "", variant: str = "primary", icon_text: str = "", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.icon_text = icon_text
        self._variant = variant
        self._base, self._hover, self._fg = self.VARIANTS.get(variant, self.VARIANTS["primary"])

        self._color = QColor(self._base)
        self._anim = QPropertyAnimation(self, b"_btn_color")
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.InOutSine)

        self.setMinimumHeight(38)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setFont(QFont("Segoe UI", 10, QFont.DemiBold))
        self._h_pad = 18
        self._refresh_style(self._color)

    def get_btn_color(self): return self._color
    def set_btn_color(self, c):
        self._color = c
        self._refresh_style(c)
    _btn_color = pyqtProperty(QColor, fget=get_btn_color, fset=set_btn_color)

    def _refresh_style(self, c: QColor):
        bg = f"rgba({c.red()},{c.green()},{c.blue()},{c.alpha()})"
        border_css = ""
        if self._variant == "outline":
            border_css = f"border: 2px solid {C['accent']};"
        self.setStyleSheet(f"""
            StyledButton {{
                background: {bg};
                color: {self._fg};
                border: none;
                {border_css}
                border-radius: 19px;
                padding: 6px {self._h_pad}px;
                font-size: 10pt;
                font-weight: 600;
            }}
            StyledButton:disabled {{
                background: {C['border']};
                color: {C['text_sec']};
                border: none;
            }}
        """)

    def enterEvent(self, e):
        if self.isEnabled():
            self._animate_to(QColor(self._hover))
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._animate_to(QColor(self._base))
        super().leaveEvent(e)

    def _animate_to(self, target: QColor):
        self._anim.stop()
        self._anim.setStartValue(self._color)
        self._anim.setEndValue(target)
        self._anim.start()

    def set_variant(self, variant: str):
        self._variant = variant
        self._base, self._hover, self._fg = self.VARIANTS.get(variant, self.VARIANTS["primary"])
        self._color = QColor(self._base)
        self._refresh_style(self._color)

    def set_compact(self, h_pad: int = 10):
        """Reduce horizontal padding — useful for small fixed-size buttons."""
        self._h_pad = h_pad
        self._refresh_style(self._color)


# ─────────────────────────────────────────────────────────────
# Pulsing status dot
# ─────────────────────────────────────────────────────────────
class StatusDot(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self._active = False
        self._opacity = 1.0
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._pulse_tick)
        self._pulse_step = 0

    def set_active(self, active: bool):
        self._active = active
        if active:
            self._pulse_timer.start(40)
        else:
            self._pulse_timer.stop()
            self._opacity = 1.0
            self.update()

    def _pulse_tick(self):
        self._pulse_step = (self._pulse_step + 3) % 360
        import math
        self._opacity = 0.45 + 0.55 * abs(math.sin(math.radians(self._pulse_step)))
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        color = QColor(C["success"] if self._active else C["text_sec"])
        color.setAlphaF(self._opacity if self._active else 0.5)
        if self._active:
            glow = QColor(C["success"])
            glow.setAlpha(60)
            p.setBrush(QBrush(glow))
            p.setPen(Qt.NoPen)
            p.drawEllipse(0, 0, 12, 12)
        p.setBrush(QBrush(color))
        p.setPen(Qt.NoPen)
        p.drawEllipse(2, 2, 8, 8)


# ─────────────────────────────────────────────────────────────
# Card frame helper
# ─────────────────────────────────────────────────────────────
class Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            Card {{
                background: {C['surface']};
                border: 1px solid {C['border']};
                border-radius: 12px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 16))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)


# ─────────────────────────────────────────────────────────────
# QR Dialog
# ─────────────────────────────────────────────────────────────
class QRDialog(QDialog):
    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scan to Connect")
        self.setFixedSize(520, 400)
        self.setStyleSheet(f"background: {C['surface']}; color: {C['text']};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Scan QR Code")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        img = qrcode.make(url, box_size=7, border=2)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        pix = QPixmap()
        pix.loadFromData(buf.read(), "PNG")

        qr_lbl = QLabel()
        qr_lbl.setPixmap(pix.scaled(420, 360, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        qr_lbl.setAlignment(Qt.AlignCenter)
        qr_lbl.setStyleSheet("background: white; border-radius: 8px; padding: 8px;")
        layout.addWidget(qr_lbl)

        url_lbl = QLabel(url)
        url_lbl.setFont(QFont("Cascadia Code", 9))
        url_lbl.setAlignment(Qt.AlignCenter)
        url_lbl.setStyleSheet(f"color: {C['accent_dark']}; background: {C['accent_soft']}; "
                              f"border-radius: 6px; padding: 6px;")
        url_lbl.setWordWrap(True)
        layout.addWidget(url_lbl)

        close_btn = StyledButton("Close", variant="ghost")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


# ─────────────────────────────────────────────────────────────
# Collapsible Settings Sidebar
# ─────────────────────────────────────────────────────────────
class SettingsSidebar(QFrame):
    SIDEBAR_W = 300

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(self.SIDEBAR_W)
        self.setStyleSheet(f"""
            SettingsSidebar {{
                background: {C['surface2']};
                border-left: 1px solid {C['border']};
                border-radius: 0;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
            QCheckBox {{
                background: transparent;
                color: {C['text']};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px; height: 18px;
                border-radius: 5px;
                border: 2px solid {C['border']};
                background: white;
            }}
            QCheckBox::indicator:checked {{
                background: {C['accent']};
                border-color: {C['accent']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 28, 24, 24)
        layout.setSpacing(18)

        header = QLabel("⚙  Settings")
        header.setFont(QFont("Segoe UI", 13, QFont.Bold))
        header.setStyleSheet(f"color: {C['text']};")
        layout.addWidget(header)

        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet(f"background: {C['border']}; max-height: 1px;")
        layout.addWidget(div)

        self.autostart_chk    = QCheckBox("Auto-start server on launch")
        self.remember_dir_chk = QCheckBox("Remember last directory")
        self.remember_dir_chk.setChecked(True)

        for chk in (self.autostart_chk, self.remember_dir_chk):
            chk.setFont(QFont("Segoe UI", 10))
            layout.addWidget(chk)

        

        self.close_btn = StyledButton("← Close", variant="ghost")
        layout.addWidget(self.close_btn)
        layout.addStretch()

# ─────────────────────────────────────────────────────────────
# URL Chip
# ─────────────────────────────────────────────────────────────
class URLChip(QFrame):
    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self.url = url
        self.setStyleSheet(f"""
            URLChip {{
                background: {C['accent_soft']};
                border: 1px solid {C['accent']};
                border-radius: 8px;
            }}
        """)
        self.setCursor(Qt.PointingHandCursor)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        lbl = QLabel(f"<a href='{url}' style='color:{C['accent_dark']}; "
                     f"text-decoration:none; font-weight:600;'>{url}</a>")
        lbl.setOpenExternalLinks(False)
        lbl.setFont(QFont("Cascadia Code", 9))
        lbl.linkActivated.connect(self._open)

        copy_btn = StyledButton("Copy", variant="outline")
        copy_btn.setFixedSize(68, 28)
        copy_btn.set_compact(10)
        copy_btn.setFont(QFont("Segoe UI", 8, QFont.DemiBold))
        copy_btn.clicked.connect(self._copy)

        layout.addWidget(lbl, 1)
        layout.addWidget(copy_btn)

    def _open(self):
        import webbrowser
        webbrowser.open(self.url)
        self._copy()

    def _copy(self):
        QApplication.clipboard().setText(self.url)
        stats_emitter.log_signal.emit(f"Copied URL: {self.url}", "info")

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._open()
        super().mousePressEvent(e)


# ─────────────────────────────────────────────────────────────
# Main Window
# ─────────────────────────────────────────────────────────────
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nova Server")
        self.resize(1000, 700)
        self.setMinimumSize(300, 300)   # scroll area absorbs anything smaller

        self.server_thread: Optional[HttpServerThread] = None
        self.start_time: Optional[float] = None
        self.current_dir = os.getcwd()
        self._full_log: list = []
        self._restart_pending = False

        self.settings = QSettings("NovaServer", "NovaServerGUI")
        self._build_ui()
        self._connect_signals()
        self._apply_global_style()
        self.restore_settings()

    # ── UI Construction ──────────────────────────────────────
    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Scroll area wraps the whole main panel so content NEVER
        #    overlaps — if the window is too small, it scrolls instead. ──
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{ background: {C['bg']}; border: none; }}
            QScrollBar:vertical {{
                background: {C['bg']}; width: 10px; border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: {C['border']}; border-radius: 5px; min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {C['accent']}; }}
        """)

        self.main_panel = QWidget()
        self.main_panel.setStyleSheet(f"background: {C['bg']};")
        ml = QVBoxLayout(self.main_panel)
        ml.setContentsMargins(28, 24, 28, 24)
        ml.setSpacing(16)

        # ── Header ───────────────────────────────────────────
        header_card = QWidget()
        header_card.setMinimumHeight(82)
        header_card.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {C['accent']}, stop:1 {C['accent_light']});
            border-radius: 14px;
        """)
        hl = QHBoxLayout(header_card)
        hl.setContentsMargins(24, 18, 24, 18)
        hl.setSpacing(14)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        self.title_lbl = QLabel("Nova Server")
        self.title_lbl.setFont(QFont("Segoe UI", 22, QFont.Bold))
        self.title_lbl.setStyleSheet("color: white; background: transparent;")
        self.subtitle_lbl = QLabel("Serve any folder over your local network instantly")
        self.subtitle_lbl.setFont(QFont("Segoe UI", 10))
        self.subtitle_lbl.setStyleSheet("color: rgba(255,255,255,0.88); background: transparent;")
        title_col.addWidget(self.title_lbl)
        title_col.addWidget(self.subtitle_lbl)
        hl.addLayout(title_col, 1)

        badge_widget = QWidget()
        badge_widget.setStyleSheet("background: transparent;")
        bl = QHBoxLayout(badge_widget)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(8)
        self.status_dot = StatusDot()
        self.status_lbl = QLabel("Stopped")
        self.status_lbl.setFont(QFont("Segoe UI", 10, QFont.DemiBold))
        self.status_lbl.setStyleSheet("color: rgba(255,255,255,0.9); background: transparent;")
        bl.addWidget(self.status_dot)
        bl.addWidget(self.status_lbl)
        hl.addWidget(badge_widget)

        self.settings_btn = StyledButton("⚙  Settings", variant="ghost")
        self.settings_btn.setStyleSheet("""
            StyledButton {
                background: rgba(255,255,255,0.20);
                color: white;
                border-radius: 19px;
                padding: 8px 16px;
                font-size: 10pt; font-weight: 600;
                border: 1px solid rgba(255,255,255,0.4);
            }
            StyledButton:hover { background: rgba(255,255,255,0.32); }
        """)
        hl.addWidget(self.settings_btn)
        ml.addWidget(header_card)

        # ── Config card (Directory / Port / Bind — each on its own row
        #    so nothing gets crowded or overlaps) ─────────────────────
        cfg_card = Card()
        cl = QVBoxLayout(cfg_card)
        cl.setContentsMargins(22, 20, 22, 20)
        cl.setSpacing(14)

        LABEL_W = 76

        def row_label(text):
            lbl = QLabel(text)
            lbl.setFont(QFont("Segoe UI", 9, QFont.DemiBold))
            lbl.setStyleSheet(f"color: {C['text_sec']}; background: transparent;")
            lbl.setFixedWidth(LABEL_W)
            return lbl

        # Row 1: Directory
        dir_row = QHBoxLayout()
        dir_row.setSpacing(10)
        self.dir_edit = self._make_lineedit("Select a folder to serve…")
        self.dir_edit.setText(self.current_dir)
        self.dir_btn = StyledButton("Browse", variant="ghost")
        self.dir_btn.setFixedHeight(36)
        self.dir_btn.setMinimumWidth(96)
        dir_row.addWidget(row_label("Directory"))
        dir_row.addWidget(self.dir_edit, 1)
        dir_row.addWidget(self.dir_btn)
        cl.addLayout(dir_row)

        # Row 2: Port
        port_row = QHBoxLayout()
        port_row.setSpacing(10)
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(int(self.settings.value("port", 8000)))
        self.port_spin.setFixedSize(100, 36)
        self.auto_port_btn = StyledButton("Auto-detect", variant="outline")
        self.auto_port_btn.setFixedHeight(36)
        self.auto_port_btn.setMinimumWidth(120)
        port_row.addWidget(row_label("Port"))
        port_row.addWidget(self.port_spin)
        port_row.addWidget(self.auto_port_btn)
        port_row.addStretch(1)
        cl.addLayout(port_row)

        # Row 3: Bind
        bind_row = QHBoxLayout()
        bind_row.setSpacing(10)
        self.host_combo = QComboBox()
        self._populate_hosts()
        self.host_combo.setFixedHeight(36)
        self.host_combo.setMinimumWidth(180)
        self.bind_all_chk = QCheckBox("All interfaces (0.0.0.0)")
        self.bind_all_chk.setChecked(True)
        self.bind_all_chk.setFont(QFont("Segoe UI", 9))
        bind_row.addWidget(row_label("Bind"))
        bind_row.addWidget(self.host_combo, 1)
        bind_row.addWidget(self.bind_all_chk)
        cl.addLayout(bind_row)

        ml.addWidget(cfg_card)

        # ── Action buttons ───────────────────────────────────
        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        self.start_btn   = StyledButton("▶  Start Server", variant="primary")
        self.stop_btn    = StyledButton("■  Stop",         variant="danger")
        self.restart_btn = StyledButton("↺  Restart",      variant="ghost")
        self.browser_btn = StyledButton("⧉  Open Browser", variant="ghost")
        self.qr_btn      = StyledButton("⊞  QR Code",      variant="outline")

        self.stop_btn.setEnabled(False)
        self.restart_btn.setEnabled(False)
        self.browser_btn.setEnabled(False)
        self.qr_btn.setEnabled(False)

        for b in (self.start_btn, self.stop_btn, self.restart_btn,
                  self.browser_btn, self.qr_btn):
            b.setMinimumWidth(128)
            action_row.addWidget(b)
        action_row.addStretch()
        ml.addLayout(action_row)

        # ── URLs card ────────────────────────────────────────
        urls_card = Card()
        ul = QVBoxLayout(urls_card)
        ul.setContentsMargins(20, 16, 20, 16)
        ul.setSpacing(10)
        urls_hdr = QLabel("Access URLs")
        urls_hdr.setFont(QFont("Segoe UI", 10, QFont.Bold))
        urls_hdr.setStyleSheet(f"color: {C['text']}; background: transparent;")
        ul.addWidget(urls_hdr)

        self.urls_panel = QWidget()
        self.urls_panel.setStyleSheet("background: transparent;")
        self.urls_layout = QVBoxLayout(self.urls_panel)
        self.urls_layout.setContentsMargins(0, 0, 0, 0)
        self.urls_layout.setSpacing(8)
        self._show_url_placeholder()
        ul.addWidget(self.urls_panel)
        ml.addWidget(urls_card)

        # ── Stats row ────────────────────────────────────────
        stats_card = Card()
        sl = QHBoxLayout(stats_card)
        sl.setContentsMargins(20, 16, 20, 16)
        sl.setSpacing(0)

        def stat_block(label):
            w = QWidget()
            w.setStyleSheet("background: transparent;")
            vl = QVBoxLayout(w)
            vl.setContentsMargins(0, 0, 0, 0)
            vl.setSpacing(2)
            val = QLabel("—")
            val.setFont(QFont("Segoe UI", 16, QFont.Bold))
            val.setStyleSheet(f"color: {C['text']}; background: transparent;")
            lbl = QLabel(label)
            lbl.setFont(QFont("Segoe UI", 9))
            lbl.setStyleSheet(f"color: {C['text_sec']}; background: transparent;")
            vl.addWidget(val)
            vl.addWidget(lbl)
            return w, val

        uptime_w, self.uptime_val = stat_block("Uptime")
        req_w,    self.req_val    = stat_block("Requests")
        bytes_w,  self.bytes_val  = stat_block("Data Served")

        blocks = (uptime_w, req_w, bytes_w)
        for i, w in enumerate(blocks):
            sl.addWidget(w, 1)
            if i < len(blocks) - 1:
                div = QFrame()
                div.setFrameShape(QFrame.VLine)
                div.setStyleSheet(f"background: {C['border']}; max-width: 1px;")
                sl.addWidget(div)

        ml.addWidget(stats_card)

        # ── Log panel ────────────────────────────────────────
        log_card = Card()
        log_card.setMinimumHeight(220)
        ll = QVBoxLayout(log_card)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.setSpacing(0)

        log_bar = QWidget()
        log_bar.setStyleSheet(f"""
            background: {C['surface']};
            border-radius: 12px 12px 0 0;
            border-bottom: 1px solid {C['border']};
        """)
        lb = QHBoxLayout(log_bar)
        lb.setContentsMargins(16, 10, 16, 10)
        lb.setSpacing(10)
        log_title = QLabel("Server Log")
        log_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        log_title.setStyleSheet(f"color: {C['text']}; background: transparent;")
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter log (regex or text)…")
        self.filter_edit.setFixedHeight(32)
        self.filter_edit.setStyleSheet(f"""
            QLineEdit {{
                background: {C['bg']};
                border: 1px solid {C['border']};
                border-radius: 8px;
                padding: 4px 10px;
                font-size: 9pt;
                color: {C['text']};
            }}
            QLineEdit:focus {{ border-color: {C['accent']}; }}
        """)
        self.clear_log_btn = StyledButton("Clear", variant="ghost")
        self.clear_log_btn.setFixedHeight(32)
        self.clear_log_btn.setMinimumWidth(70)
        lb.addWidget(log_title)
        lb.addStretch()
        lb.addWidget(self.filter_edit, 1)
        lb.addWidget(self.clear_log_btn)
        ll.addWidget(log_bar)

        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setFont(QFont("Cascadia Code", 9))
        self.log_edit.setMinimumHeight(170)
        self.log_edit.setStyleSheet(f"""
            QTextEdit {{
                background: {C['log_bg']};
                color: {C['log_text']};
                border: none;
                border-radius: 0 0 12px 12px;
                padding: 12px;
                selection-background-color: {C['accent']};
            }}
            QScrollBar:vertical {{
                background: #16301F; width: 8px; border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: #2C5B3D; border-radius: 4px; min-height: 24px;
            }}
        """)
        self.log_edit.setPlaceholderText("Log output will appear here when the server starts…")
        ll.addWidget(self.log_edit, 1)
        ml.addWidget(log_card, 1)

        self.scroll.setWidget(self.main_panel)

        # ── Settings sidebar ─────────────────────────────────
        self.sidebar = SettingsSidebar()

        # ── Root layout ──────────────────────────────────────
        root.addWidget(self.scroll, 1)
        root.addWidget(self.sidebar)
        self.sidebar.setVisible(False)
        self._sidebar_visible = False

        # Timers
        self._uptime_timer = QTimer(self)
        self._uptime_timer.setInterval(1000)
        self._uptime_timer.timeout.connect(self._tick_uptime)

    # ── Style sheet ──────────────────────────────────────────
    def _apply_global_style(self):
        self.setStyleSheet(f"""
            QWidget {{
                background: {C['bg']};
                color: {C['text']};
                font-family: 'Segoe UI', 'Inter', sans-serif;
                font-size: 10pt;
            }}
            QSpinBox {{
                background: {C['surface']};
                border: 1px solid {C['border']};
                border-radius: 8px;
                padding: 4px 8px;
                color: {C['text']};
                selection-background-color: {C['accent']};
            }}
            QSpinBox:focus {{ border-color: {C['accent']}; }}
            QComboBox {{
                background: {C['surface']};
                border: 1px solid {C['border']};
                border-radius: 8px;
                padding: 4px 8px;
                color: {C['text']};
            }}
            QComboBox:focus {{ border-color: {C['accent']}; }}
            QComboBox::drop-down {{ border: none; }}
            QCheckBox {{
                color: {C['text']};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px; height: 18px;
                border-radius: 5px;
                border: 2px solid {C['border']};
                background: {C['surface']};
            }}
            QCheckBox::indicator:checked {{
                background: {C['accent']};
                border-color: {C['accent']};
            }}
            QScrollArea {{ border: none; background: transparent; }}
        """)

    # ── Helpers ──────────────────────────────────────────────
    def _make_lineedit(self, placeholder=""):
        le = QLineEdit()
        le.setPlaceholderText(placeholder)
        le.setFixedHeight(36)
        le.setStyleSheet(f"""
            QLineEdit {{
                background: {C['surface']};
                border: 1px solid {C['border']};
                border-radius: 8px;
                padding: 4px 10px;
                color: {C['text']};
                selection-background-color: {C['accent']};
            }}
            QLineEdit:focus {{ border-color: {C['accent']}; }}
        """)
        return le

    def _populate_hosts(self):
        self.host_combo.clear()
        for ip in get_all_ips():
            self.host_combo.addItem(ip)

    def _show_url_placeholder(self):
        self._clear_urls()
        ph = QLabel("Server not running — start the server to see access URLs.")
        ph.setFont(QFont("Segoe UI", 9))
        ph.setStyleSheet(f"color: {C['text_sec']}; background: transparent;")
        self.urls_layout.addWidget(ph)

    def _clear_urls(self):
        while self.urls_layout.count():
            item = self.urls_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # ── Signal wiring ────────────────────────────────────────
    def _connect_signals(self):
        self.dir_btn.clicked.connect(self._browse_dir)
        self.auto_port_btn.clicked.connect(self._auto_port)
        self.start_btn.clicked.connect(self.start_server)
        self.stop_btn.clicked.connect(self.stop_server)
        self.restart_btn.clicked.connect(self._restart_server)
        self.browser_btn.clicked.connect(self._open_browser)
        self.qr_btn.clicked.connect(self._show_qr)
        self.settings_btn.clicked.connect(self._toggle_sidebar)
        self.sidebar.close_btn.clicked.connect(self._toggle_sidebar)
        self.filter_edit.textChanged.connect(self._apply_filter)
        self.clear_log_btn.clicked.connect(self._clear_log)
        self.bind_all_chk.stateChanged.connect(
            lambda _: self.host_combo.setEnabled(not self.bind_all_chk.isChecked())
        )
        stats_emitter.log_signal.connect(self._on_log)
        stats_emitter.stats_signal.connect(self._on_stats)

    # ── Actions ──────────────────────────────────────────────
    def _browse_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Select Folder to Serve",
                                             self.dir_edit.text() or os.getcwd())
        if d:
            self.dir_edit.setText(d)

    def _auto_port(self):
        p = find_free_port()
        if p:
            self.port_spin.setValue(p)
            self._log_line(f"Auto-selected port {p}", "info")
        else:
            QMessageBox.warning(self, "No Free Port", "Could not find a free port in range 8000–9000.")

    def start_server(self):
        if self.server_thread and self.server_thread.isRunning():
            return
        directory = self.dir_edit.text().strip()
        if not directory or not os.path.isdir(directory):
            QMessageBox.warning(self, "Invalid Directory", "Please select a valid directory to serve.")
            return
        host = "0.0.0.0" if self.bind_all_chk.isChecked() else self.host_combo.currentText()
        port = self.port_spin.value()

        self.server_thread = HttpServerThread(directory, host, port)
        self.server_thread.started_signal.connect(self._on_server_started)
        self.server_thread.stopped_signal.connect(self._on_server_stopped)
        self.server_thread.error_signal.connect(self._on_server_error)
        self.server_thread.start()

        self.start_btn.setEnabled(False)
        self._log_line(f"Starting server on {host}:{port}  →  {directory}", "info")

    def stop_server(self):
        if not self.server_thread:
            return
        self._log_line("Stopping server…", "warn")
        self.stop_btn.setEnabled(False)
        self.restart_btn.setEnabled(False)
        self.server_thread.stop()
        QTimer.singleShot(80, self._poll_stopped)

    def _poll_stopped(self):
        if self.server_thread and self.server_thread.isRunning():
            QTimer.singleShot(100, self._poll_stopped)

    def _restart_server(self):
        if self.server_thread and self.server_thread.isRunning():
            self._restart_pending = True
            self.stop_server()
        else:
            self.start_server()

    def _open_browser(self):
        if not self.server_thread:
            return
        import webbrowser
        host = "127.0.0.1" if self.bind_all_chk.isChecked() else self.host_combo.currentText()
        webbrowser.open(f"http://{host}:{self.port_spin.value()}")

    def _show_qr(self):
        if not HAS_QR:
            QMessageBox.information(self, "QR Code",
                "Install the 'qrcode' and 'pillow' packages:\n\n  pip install qrcode pillow")
            return
        if not self.server_thread:
            return
        host = get_primary_ip() if self.bind_all_chk.isChecked() else self.host_combo.currentText()
        url  = f"http://{host}:{self.port_spin.value()}"
        dlg  = QRDialog(url, self)
        dlg.exec_()

    # ── Server event handlers ────────────────────────────────
    def _on_server_started(self):
        self.start_time = time.time()
        self._uptime_timer.start()
        self.status_dot.set_active(True)
        self.status_lbl.setText("Running")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.restart_btn.setEnabled(True)
        self.browser_btn.setEnabled(True)
        self.qr_btn.setEnabled(HAS_QR)
        self._update_urls()
        self._log_line("Server started successfully.", "info")
        self._save_settings()

    def _on_server_stopped(self):
        self._uptime_timer.stop()
        self.status_dot.set_active(False)
        self.status_lbl.setText("Stopped")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.restart_btn.setEnabled(False)
        self.browser_btn.setEnabled(False)
        self.qr_btn.setEnabled(False)
        self.uptime_val.setText("—")
        self.req_val.setText("—")
        self.bytes_val.setText("—")
        self._show_url_placeholder()
        self.server_thread = None
        self._log_line("Server stopped.", "warn")

        if self._restart_pending:
            self._restart_pending = False
            QTimer.singleShot(200, self.start_server)

    def _on_server_error(self, err: str):
        self._log_line(f"ERROR: {err}", "error")
        QMessageBox.critical(self, "Server Error",
            f"Failed to start the server:\n\n{err}\n\nTry a different port.")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.restart_btn.setEnabled(False)
        self.server_thread = None

    # ── URL display ──────────────────────────────────────────
    def _update_urls(self):
        self._clear_urls()
        port = self.port_spin.value()
        urls = []
        if self.bind_all_chk.isChecked():
            urls.append(f"http://127.0.0.1:{port}")
            urls.append(f"http://{get_primary_ip()}:{port}")
        else:
            urls.append(f"http://{self.host_combo.currentText()}:{port}")

        for url in urls:
            chip = URLChip(url)
            self.urls_layout.addWidget(chip)

    # ── Logging ──────────────────────────────────────────────
    def _log_line(self, text: str, level: str = "info"):
        ts = time.strftime("%H:%M:%S")
        line = f"[{ts}] {text}"
        self._full_log.append((line, level))
        self._append_to_log(line, level)

    @pyqtSlot(str, str)
    def _on_log(self, msg: str, level: str):
        self._full_log.append((msg, level))
        filt = self.filter_edit.text().strip()
        if not filt or self._matches_filter(msg, filt):
            self._append_to_log(msg, level)

    def _append_to_log(self, line: str, level: str):
        colors = {
            "info":  C["log_text"],
            "warn":  C["warn"],
            "error": C["log_error"],
        }
        color = colors.get(level, C["log_text"])
        import html
        safe = html.escape(line)
        safe = re.sub(
            r"^(\[\d{2}:\d{2}:\d{2}\])",
            f'<span style="color:{C["log_ts"]}">\\1</span>',
            safe
        )
        self.log_edit.append(f'<span style="color:{color}">{safe}</span>')
        sb = self.log_edit.verticalScrollBar()
        sb.setValue(sb.maximum())

    @pyqtSlot(int, int)
    def _on_stats(self, reqs: int, byt: int):
        self.req_val.setText(str(reqs))
        self.bytes_val.setText(self._human_size(byt))

    def _clear_log(self):
        self._full_log.clear()
        self.log_edit.clear()

    def _apply_filter(self):
        filt = self.filter_edit.text().strip()
        self.log_edit.clear()
        for line, level in self._full_log:
            if not filt or self._matches_filter(line, filt):
                self._append_to_log(line, level)

    def _matches_filter(self, line: str, filt: str) -> bool:
        try:
            return bool(re.search(filt, line))
        except re.error:
            return filt.lower() in line.lower()

    # ── Uptime tick ──────────────────────────────────────────
    def _tick_uptime(self):
        if not self.start_time:
            return
        elapsed = int(time.time() - self.start_time)
        h, rem = divmod(elapsed, 3600)
        m, s   = divmod(rem, 60)
        self.uptime_val.setText(f"{h:02d}:{m:02d}:{s:02d}")

    # ── Sidebar toggle ───────────────────────────────────────
    def _toggle_sidebar(self):
        self._sidebar_visible = not self._sidebar_visible
        self.sidebar.setVisible(self._sidebar_visible)

    # ── Helpers ──────────────────────────────────────────────
    def _human_size(self, num: float) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if num < 1024:
                return f"{num:.1f} {unit}"
            num /= 1024
        return f"{num:.1f} PB"

    # ── Persistence ──────────────────────────────────────────
    def _save_settings(self):
        self.settings.setValue("port",         self.port_spin.value())
        self.settings.setValue("remember_dir", self.sidebar.remember_dir_chk.isChecked())
        self.settings.setValue("autostart",    self.sidebar.autostart_chk.isChecked())
        if self.sidebar.remember_dir_chk.isChecked():
            self.settings.setValue("last_dir", self.dir_edit.text())

    def restore_settings(self):
        self.port_spin.setValue(int(self.settings.value("port", 8000)))
        remember = self.settings.value("remember_dir", True, type=bool)
        self.sidebar.remember_dir_chk.setChecked(remember)
        self.sidebar.autostart_chk.setChecked(
            self.settings.value("autostart", False, type=bool))
        if remember:
            last = self.settings.value("last_dir", "", type=str)
            if last and os.path.isdir(last):
                self.dir_edit.setText(last)
        if self.sidebar.autostart_chk.isChecked():
            QTimer.singleShot(400, self.start_server)

    # ── Window close ─────────────────────────────────────────
    def closeEvent(self, e):
        if self.server_thread and self.server_thread.isRunning():
            ans = QMessageBox.question(
                self, "Exit — Server Running",
                "The server is still running.\nStop it and exit?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes
            )
            if ans == QMessageBox.Yes:
                self.stop_server()
                t0 = time.time()
                while (self.server_thread and
                       self.server_thread.isRunning() and
                       time.time() - t0 < 2.5):
                    QApplication.processEvents()
                    time.sleep(0.04)
            elif ans == QMessageBox.Cancel:
                e.ignore()
                return
        self._save_settings()
        super().closeEvent(e)


# ─────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────
def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Nova Server")
    app.setOrganizationName("NovaServer")

    pal = app.palette()
    pal.setColor(QPalette.Window,          QColor(C["bg"]))
    pal.setColor(QPalette.WindowText,      QColor(C["text"]))
    pal.setColor(QPalette.Base,            QColor(C["surface"]))
    pal.setColor(QPalette.AlternateBase,   QColor(C["surface2"]))
    pal.setColor(QPalette.Text,            QColor(C["text"]))
    pal.setColor(QPalette.Button,          QColor(C["surface"]))
    pal.setColor(QPalette.ButtonText,      QColor(C["text"]))
    pal.setColor(QPalette.Highlight,       QColor(C["accent"]))
    pal.setColor(QPalette.HighlightedText, QColor(C["text_inv"]))
    app.setPalette(pal)

    w = MainWindow()
    w.show()
    sys.exit(app.exec_())

##
if __name__ == "__main__":
    main()