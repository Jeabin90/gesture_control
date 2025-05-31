import json
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QFormLayout,
    QLineEdit, QPushButton, QTextEdit, QStatusBar, QLabel,
    QSlider, QHBoxLayout
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap, QImage

class GestureControlUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PC Gesture Control")
        self.setGeometry(100, 100, 800, 700)  # 크기 키움
        self.settings_path = "settings.json"
        self.dark_mode = False
        self.init_ui()
        self.load_settings()
        self.fps = 0

        self.fade_in()

    def fade_in(self):
        self.setWindowOpacity(0)
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(1000)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.anim.start()

    def init_ui(self):
        main_layout = QVBoxLayout()

        self.status_bar = QStatusBar()
        self.status_label = QLabel("상태: 정상")
        self.mode_label = QLabel("모드: 대기 중")
        self.fps_label = QLabel("FPS: 0")

        self.status_bar.addWidget(self.status_label)
        self.status_bar.addWidget(self.mode_label)
        self.status_bar.addPermanentWidget(self.fps_label)
        main_layout.addWidget(self.status_bar)

        # 카메라 화면 QLabel
        self.camera_label = QLabel("카메라 화면 준비 중...")
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setStyleSheet("background-color: #000; border: 1px solid #ccc;")
        main_layout.addWidget(self.camera_label)

        self.tabs = QTabWidget()
        self.settings_tab = QWidget()
        self.log_tab = QWidget()
        self.tabs.addTab(self.settings_tab, "설정")
        self.tabs.addTab(self.log_tab, "로그")
        main_layout.addWidget(self.tabs)

        self.init_settings_tab()
        self.init_log_tab()

        self.setLayout(main_layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)

    def init_settings_tab(self):
        form_layout = QFormLayout()

        self.vgesture_command_line = QLineEdit()
        self.vgesture_command_line.setPlaceholderText("예: notepad.exe")
        form_layout.addRow("V자 제스처 앱 실행 명령:", self.vgesture_command_line)

        sensitivity_layout = QHBoxLayout()
        self.sensitivity_slider = QSlider(Qt.Orientation.Horizontal)
        self.sensitivity_slider.setMinimum(10)
        self.sensitivity_slider.setMaximum(50)
        self.sensitivity_slider.setValue(20)
        self.sensitivity_slider.valueChanged.connect(self.update_sensitivity_label)

        self.sensitivity_label = QLabel("40%")
        self.reset_sensitivity_btn = QPushButton("초기화")
        self.reset_sensitivity_btn.clicked.connect(self.reset_sensitivity)

        sensitivity_layout.addWidget(self.sensitivity_slider)
        sensitivity_layout.addWidget(self.sensitivity_label)
        sensitivity_layout.addWidget(self.reset_sensitivity_btn)

        form_layout.addRow("마우스 이동 감도:", sensitivity_layout)

        self.toggle_theme_btn = QPushButton("다크모드 켜기")
        self.toggle_theme_btn.clicked.connect(self.toggle_theme)
        form_layout.addRow("테마 설정:", self.toggle_theme_btn)

        self.save_settings_btn = QPushButton("설정 저장")
        self.save_settings_btn.clicked.connect(self.save_settings)
        form_layout.addRow("", self.save_settings_btn)

        self.reset_all_btn = QPushButton("설정 초기화")
        self.reset_all_btn.clicked.connect(self.reset_all_settings)
        form_layout.addRow("", self.reset_all_btn)

        self.settings_tab.setLayout(form_layout)

    def init_log_tab(self):
        layout = QVBoxLayout()
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        layout.addWidget(self.log_text_edit)
        self.log_tab.setLayout(layout)

    def save_settings(self):
        settings = {
            "vgesture_command": self.vgesture_command_line.text(),
            "sensitivity": self.sensitivity_slider.value(),
            "dark_mode": self.dark_mode
        }
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)

        sensitivity_percent = int((self.sensitivity_slider.value() / 50) * 100)
        self.update_log(f"설정 저장됨: V자 앱 명령 - {settings['vgesture_command']}, 감도 - {sensitivity_percent}%, 다크모드 - {settings['dark_mode']}")

    def load_settings(self):
        if not os.path.exists(self.settings_path):
            return

        with open(self.settings_path, "r", encoding="utf-8") as f:
            settings = json.load(f)

        self.vgesture_command_line.setText(settings.get("vgesture_command", ""))
        self.sensitivity_slider.setValue(settings.get("sensitivity", 20))

        if settings.get("dark_mode", False):
            self.apply_dark_theme()
            self.dark_mode = True
            self.toggle_theme_btn.setText("라이트모드 켜기")

    def reset_all_settings(self):
        self.vgesture_command_line.clear()
        self.sensitivity_slider.setValue(20)
        self.update_sensitivity_label()

        if self.dark_mode:
            self.apply_light_theme()
            self.dark_mode = False
            self.toggle_theme_btn.setText("다크모드 켜기")

        if os.path.exists(self.settings_path):
            os.remove(self.settings_path)

        self.update_log("🛠️ 모든 설정 초기화 완료")

    def update_log(self, text):
        self.log_text_edit.append(text)

    def update_status(self):
        self.fps += 1
        self.fps_label.setText(f"FPS: {self.fps}")

    def update_mode(self, mode_text):
        self.mode_label.setText(f"모드: {mode_text}")

    def update_sensitivity_label(self):
        value = self.sensitivity_slider.value()
        percent = int((value / 50) * 100)
        self.sensitivity_label.setText(f"{percent}%")

    def reset_sensitivity(self):
        self.sensitivity_slider.setValue(20)
        self.update_sensitivity_label()
        self.update_log("감도 초기화 (40%) 완료")

    def get_sensitivity(self):
        return self.sensitivity_slider.value() / 100.0

    def toggle_theme(self):
        if not self.dark_mode:
            self.apply_dark_theme()
            self.dark_mode = True
            self.toggle_theme_btn.setText("라이트모드 켜기")
            self.update_log("🌙 다크모드 적용")
        else:
            self.apply_light_theme()
            self.dark_mode = False
            self.toggle_theme_btn.setText("다크모드 켜기")
            self.update_log("☀️ 라이트모드 복구")

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QWidget { background-color: #2c2c2c; color: #f0f0f0; }
            QPushButton { background-color: #555; color: #fff; border: 1px solid #777; padding: 5px; }
            QPushButton:hover { background-color: #777; }
            QLineEdit { background-color: #444; color: #fff; border: 1px solid #666; }
            QSlider::groove:horizontal { background: #444; }
            QSlider::handle:horizontal { background: #bbb; border: 1px solid #999; width: 10px; margin: -2px 0; }
            QTextEdit { background-color: #333; color: #ddd; }
            QTabWidget::pane { border: 1px solid #444; }
            QTabBar::tab { background: #333; color: #ccc; padding: 5px; }
            QTabBar::tab:selected { background: #555; color: white; }
        """)

    def apply_light_theme(self):
        self.setStyleSheet("""
            QWidget { background-color: #f5f5f5; color: #333; }
            QPushButton { background-color: #4CAF50; color: white; border-radius: 5px; padding: 8px; }
            QPushButton:hover { background-color: #45a049; }
            QLineEdit { background-color: #ffffff; color: #000000; border: 1px solid #ccc; padding: 5px; }
            QSlider::groove:horizontal { background: #ddd; }
            QSlider::handle:horizontal { background: #4CAF50; border: 1px solid #4CAF50; width: 12px; margin: -2px 0; }
            QTextEdit { background-color: #ffffff; color: #000; }
            QTabWidget::pane { border: 1px solid #ccc; }
            QTabBar::tab { background: #e0e0e0; color: #333; padding: 5px; }
            QTabBar::tab:selected { background: #4CAF50; color: white; }
        """)

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = GestureControlUI()
    window.show()
    sys.exit(app.exec())
