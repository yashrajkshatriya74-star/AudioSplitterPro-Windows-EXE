"""
Audio Splitter Pro
-------------------
A local Windows desktop app to split audio files into equal-length
chunks (10s / 15s / 20s / custom), with waveform preview and playback.

Run:
    pip install -r requirements.txt
    python main.py

Build a standalone .exe (on Windows):
    build_exe.bat
"""

import os
import sys
import math
import numpy as np

from PySide6.QtCore import Qt, QUrl, QTimer, QSize
from PySide6.QtGui import QFont, QPainter, QColor, QPen, QLinearGradient, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QDial, QSlider, QSplashScreen,
    QFrame, QSizePolicy, QMessageBox, QProgressBar, QSpinBox, QComboBox
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from pydub import AudioSegment

APP_NAME = "Audio Splitter Pro"

# ---------------------------------------------------------------------
# THEME - Dark Ocean Blue
# ---------------------------------------------------------------------
BG_DARK = "#061821"
BG_PANEL = "#0c2733"
BG_PANEL_2 = "#0f3140"
ACCENT = "#2bd4c8"
ACCENT_2 = "#1e9bb5"
TEXT_MAIN = "#dff6f5"
TEXT_DIM = "#7ea9b0"
DANGER = "#ff6b6b"

STYLE_SHEET = f"""
QWidget {{
    background-color: {BG_DARK};
    color: {TEXT_MAIN};
    font-family: 'Segoe UI', Arial;
    font-size: 13px;
}}
QFrame#panel {{
    background-color: {BG_PANEL};
    border-radius: 10px;
    border: 1px solid {BG_PANEL_2};
}}
QPushButton {{
    background-color: {BG_PANEL_2};
    color: {TEXT_MAIN};
    border: 1px solid {ACCENT_2};
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: {ACCENT_2};
    color: {BG_DARK};
}}
QPushButton:pressed {{
    background-color: {ACCENT};
    color: {BG_DARK};
}}
QPushButton#primary {{
    background-color: {ACCENT};
    color: {BG_DARK};
    border: none;
}}
QPushButton#primary:hover {{
    background-color: {ACCENT_2};
}}
QPushButton#export {{
    background-color: {ACCENT_2};
    color: {BG_DARK};
    font-weight: 700;
    border-radius: 18px;
    padding: 8px 20px;
}}
QLabel#title {{
    color: {ACCENT};
    font-size: 20px;
    font-weight: 700;
}}
QLabel#dim {{
    color: {TEXT_DIM};
}}
QDial {{
    background-color: {BG_PANEL_2};
}}
QSlider::groove:horizontal {{
    height: 6px;
    background: {BG_PANEL_2};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {ACCENT};
    width: 14px;
    border-radius: 7px;
    margin: -5px 0;
}}
QSlider::sub-page:horizontal {{
    background: {ACCENT_2};
    border-radius: 3px;
}}
QProgressBar {{
    background-color: {BG_PANEL_2};
    border-radius: 6px;
    text-align: center;
    color: {TEXT_MAIN};
}}
QProgressBar::chunk {{
    background-color: {ACCENT};
    border-radius: 6px;
}}
QSpinBox {{
    background-color: {BG_PANEL_2};
    border: 1px solid {ACCENT_2};
    border-radius: 6px;
    padding: 4px;
}}
QComboBox {{
    background-color: {BG_PANEL_2};
    border: 1px solid {ACCENT_2};
    border-radius: 6px;
    padding: 5px;
}}
QComboBox QAbstractItemView {{
    background-color: {BG_PANEL_2};
    selection-background-color: {ACCENT_2};
    color: {TEXT_MAIN};
}}
"""


# ---------------------------------------------------------------------
# Waveform widget (top-right display, animates while playing)
# ---------------------------------------------------------------------
class WaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.samples = None          # downsampled amplitude envelope (0..1)
        self.progress = 0.0          # 0..1 playhead position
        self.setMinimumHeight(140)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def set_samples(self, samples: np.ndarray):
        self.samples = samples
        self.progress = 0.0
        self.update()

    def set_progress(self, value: float):
        self.progress = max(0.0, min(1.0, value))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()

        # background
        grad = QLinearGradient(0, 0, 0, rect.height())
        grad.setColorAt(0, QColor(BG_PANEL_2))
        grad.setColorAt(1, QColor(BG_PANEL))
        painter.fillRect(rect, grad)

        if self.samples is None or len(self.samples) == 0:
            painter.setPen(QColor(TEXT_DIM))
            painter.drawText(rect, Qt.AlignCenter, "No audio loaded")
            return

        n = len(self.samples)
        w = rect.width()
        h = rect.height()
        mid = h / 2
        bar_w = max(1.0, w / n)

        played_bars = int(self.progress * n)

        for i, amp in enumerate(self.samples):
            x = i * bar_w
            bar_h = max(2.0, amp * (h * 0.85))
            color = QColor(ACCENT) if i <= played_bars else QColor(ACCENT_2)
            color.setAlpha(255 if i <= played_bars else 140)
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawRect(int(x), int(mid - bar_h / 2), max(1, int(bar_w - 1)), int(bar_h))

        # playhead line
        px = int(self.progress * w)
        pen = QPen(QColor(DANGER))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawLine(px, 0, px, h)


# ---------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(980, 560)

        self.audio_path = None
        self.audio_segment = None       # pydub AudioSegment
        self.duration_ms = 0
        self.split_seconds = 10

        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)

        self._build_ui()

    # ---------------- UI ----------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 16, 20, 20)
        root.setSpacing(14)

        # Header
        header = QHBoxLayout()
        title = QLabel(APP_NAME)
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch()
        self.export_btn = QPushButton("⬆  Export Clips")
        self.export_btn.setObjectName("export")
        self.export_btn.clicked.connect(self.export_clips)
        self.export_btn.setEnabled(False)
        header.addWidget(self.export_btn)
        root.addLayout(header)

        # Body: left controls | right waveform
        body = QHBoxLayout()
        body.setSpacing(16)
        root.addLayout(body, 1)

        # ----- LEFT PANEL -----
        left = QFrame()
        left.setObjectName("panel")
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(18, 18, 18, 18)
        left_l.setSpacing(14)

        self.file_label = QLabel("No file selected")
        self.file_label.setObjectName("dim")
        self.file_label.setWordWrap(True)

        open_btn = QPushButton("📂  Select Audio File")
        open_btn.setObjectName("primary")
        open_btn.clicked.connect(self.select_file)

        left_l.addWidget(open_btn)
        left_l.addWidget(self.file_label)

        # Play controls
        play_row = QHBoxLayout()
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(46, 46)
        self.play_btn.clicked.connect(self.toggle_play)
        self.play_btn.setEnabled(False)
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setObjectName("dim")
        play_row.addWidget(self.play_btn)
        play_row.addWidget(self.time_label)
        play_row.addStretch()
        left_l.addLayout(play_row)

        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, 0)
        self.seek_slider.sliderMoved.connect(self.seek)
        left_l.addWidget(self.seek_slider)

        left_l.addSpacing(10)
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"background-color:{BG_PANEL_2};")
        left_l.addWidget(divider)
        left_l.addSpacing(6)

        # Interval dial ("dialer")
        dial_label = QLabel("Split Interval (seconds)")
        dial_label.setObjectName("dim")
        left_l.addWidget(dial_label)

        dial_row = QHBoxLayout()
        self.dial = QDial()
        self.dial.setRange(5, 120)
        self.dial.setNotchesVisible(True)
        self.dial.setValue(10)
        self.dial.setFixedSize(120, 120)
        self.dial.valueChanged.connect(self.on_dial_changed)

        dial_col = QVBoxLayout()
        self.dial_value_label = QLabel("10 sec")
        self.dial_value_label.setAlignment(Qt.AlignCenter)
        self.dial_value_label.setStyleSheet(f"color:{ACCENT}; font-size:18px; font-weight:700;")
        self.spin = QSpinBox()
        self.spin.setRange(5, 600)
        self.spin.setValue(10)
        self.spin.setSuffix(" sec")
        self.spin.valueChanged.connect(self.on_spin_changed)
        dial_col.addWidget(self.dial_value_label)
        dial_col.addWidget(self.spin)

        dial_row.addWidget(self.dial)
        dial_row.addSpacing(10)
        dial_row.addLayout(dial_col)
        left_l.addLayout(dial_row)

        self.ok_btn = QPushButton("OK — Preview Split")
        self.ok_btn.clicked.connect(self.preview_split)
        self.ok_btn.setEnabled(False)
        left_l.addWidget(self.ok_btn)

        format_row = QHBoxLayout()
        format_label = QLabel("Export format:")
        format_label.setObjectName("dim")
        self.format_combo = QComboBox()
        self.format_combo.addItems(["wav", "mp3", "m4a", "flac", "ogg"])
        format_row.addWidget(format_label)
        format_row.addWidget(self.format_combo)
        format_row.addStretch()
        left_l.addLayout(format_row)

        self.preview_label = QLabel("")
        self.preview_label.setObjectName("dim")
        self.preview_label.setWordWrap(True)
        left_l.addWidget(self.preview_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_l.addWidget(self.progress_bar)

        left_l.addStretch()
        body.addWidget(left, 1)

        # ----- RIGHT PANEL (waveform) -----
        right = QFrame()
        right.setObjectName("panel")
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(14, 14, 14, 14)
        wf_title = QLabel("Waveform")
        wf_title.setObjectName("dim")
        right_l.addWidget(wf_title)
        self.waveform = WaveformWidget()
        right_l.addWidget(self.waveform, 1)
        body.addWidget(right, 2)

        # timer to sync waveform playhead
        self.ui_timer = QTimer()
        self.ui_timer.setInterval(100)
        self.ui_timer.timeout.connect(self.update_playhead)
        self.ui_timer.start()

    # ---------------- File handling ----------------
    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File", "",
            "Audio Files (*.mp3 *.wav *.m4a *.flac *.ogg *.aac);;All Files (*)"
        )
        if not path:
            return
        self.load_file(path)

    def load_file(self, path):
        try:
            self.audio_segment = AudioSegment.from_file(path)
        except Exception as e:
            QMessageBox.critical(self, "Error",
                                  f"Could not load audio.\n\nMake sure ffmpeg is installed.\n\n{e}")
            return

        self.audio_path = path
        self.duration_ms = len(self.audio_segment)
        self.file_label.setText(os.path.basename(path))
        self.play_btn.setEnabled(True)
        self.ok_btn.setEnabled(True)
        self.export_btn.setEnabled(False)
        self.preview_label.setText("")

        self.player.setSource(QUrl.fromLocalFile(path))

        # Build downsampled waveform envelope for display
        samples = np.array(self.audio_segment.get_array_of_samples()).astype(np.float32)
        if self.audio_segment.channels > 1:
            samples = samples.reshape((-1, self.audio_segment.channels)).mean(axis=1)
        samples = np.abs(samples)
        max_val = samples.max() if samples.max() > 0 else 1
        samples = samples / max_val

        n_bars = 220
        chunk = max(1, len(samples) // n_bars)
        envelope = np.array([samples[i:i + chunk].mean() for i in range(0, len(samples), chunk)])
        envelope = envelope[:n_bars]
        self.waveform.set_samples(envelope)

        self.preview_split()

    # ---------------- Playback ----------------
    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.play_btn.setText("▶")
        else:
            self.player.play()
            self.play_btn.setText("⏸")

    def on_duration_changed(self, dur):
        self.seek_slider.setRange(0, dur)

    def on_position_changed(self, pos):
        self.seek_slider.blockSignals(True)
        self.seek_slider.setValue(pos)
        self.seek_slider.blockSignals(False)
        self.time_label.setText(f"{self.fmt(pos)} / {self.fmt(self.player.duration())}")
        if self.player.playbackState() != QMediaPlayer.PlayingState and pos == 0:
            self.play_btn.setText("▶")

    def seek(self, pos):
        self.player.setPosition(pos)

    def update_playhead(self):
        dur = self.player.duration()
        if dur > 0:
            self.waveform.set_progress(self.player.position() / dur)
        if self.player.playbackState() == QMediaPlayer.StoppedState:
            self.play_btn.setText("▶")

    @staticmethod
    def fmt(ms):
        s = int(ms / 1000)
        return f"{s // 60:02d}:{s % 60:02d}"

    # ---------------- Split interval controls ----------------
    def on_dial_changed(self, value):
        self.split_seconds = value
        self.dial_value_label.setText(f"{value} sec")
        self.spin.blockSignals(True)
        self.spin.setValue(value)
        self.spin.blockSignals(False)

    def on_spin_changed(self, value):
        self.split_seconds = value
        self.dial_value_label.setText(f"{value} sec")
        if value <= 120:
            self.dial.blockSignals(True)
            self.dial.setValue(value)
            self.dial.blockSignals(False)

    def preview_split(self):
        if not self.audio_segment:
            return
        total_sec = self.duration_ms / 1000
        n_clips = math.ceil(total_sec / self.split_seconds)
        self.preview_label.setText(
            f"Audio length: {self.fmt(self.duration_ms)}  →  "
            f"Will create {n_clips} clip(s) of {self.split_seconds}s each."
        )
        self.export_btn.setEnabled(True)

    # ---------------- Export ----------------
    def export_clips(self):
        if not self.audio_segment:
            return
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Save Clips")
        if not folder:
            return

        base_name = os.path.splitext(os.path.basename(self.audio_path))[0]
        ext = self.format_combo.currentText()
        chunk_ms = self.split_seconds * 1000
        total_ms = len(self.audio_segment)
        n_clips = math.ceil(total_ms / chunk_ms)

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, n_clips)
        self.progress_bar.setValue(0)

        try:
            for i in range(n_clips):
                start = i * chunk_ms
                end = min(start + chunk_ms, total_ms)
                clip = self.audio_segment[start:end]
                out_path = os.path.join(folder, f"{base_name}_part{i+1:03d}.{ext}")
                clip.export(out_path, format=ext)
                self.progress_bar.setValue(i + 1)
                QApplication.processEvents()
        except Exception as e:
            QMessageBox.critical(
                self, "Export failed",
                f"{e}\n\nIf you selected mp3/m4a/ogg, make sure FFmpeg "
                f"is installed and added to your Windows PATH."
            )
            return
        finally:
            self.progress_bar.setVisible(False)

        QMessageBox.information(
            self, "Done",
            f"Exported {n_clips} clip(s) to:\n{folder}"
        )


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE_SHEET)

    # Splash screen with app name
    splash_pix = QSize(420, 220)
    splash = QSplashScreen()
    splash.setFixedSize(splash_pix)
    splash.setStyleSheet(f"background-color: {BG_PANEL}; border: 2px solid {ACCENT};")
    splash.showMessage(
        f"\n\n{APP_NAME}\n\nLoading...",
        Qt.AlignCenter, QColor(ACCENT)
    )
    font = QFont("Segoe UI", 16, QFont.Bold)
    splash.setFont(font)
    splash.show()
    app.processEvents()

    win = MainWindow()

    def show_main():
        splash.close()
        win.show()

    QTimer.singleShot(1400, show_main)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
