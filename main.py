import sys
import os
import json
import subprocess
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QScrollArea,
    QSlider, QLabel, QStatusBar, QMessageBox, QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QGuiApplication

class CommandApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # Get screen geometry and calculate window dimensions/position:
        screen_rect = QGuiApplication.primaryScreen().availableGeometry()
        screen_width = screen_rect.width()
        screen_height = screen_rect.height()
        window_width = screen_width // 8
        window_height = screen_height
        x = screen_width - window_width  # snapped to right edge
        y = 0
        self.setGeometry(x, y, window_width, window_height)
        self.setWindowTitle("SLACKER IT - AI Suite")
        self.apply_dark_theme()

        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # Header image at the top
        header_label = QLabel()
        pixmap = QPixmap("slackITbnr.png")
        header_label.setPixmap(pixmap)
        header_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header_label)

        # Scroll area for JSON entries
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.entries_container = QWidget()
        self.entries_layout = QVBoxLayout(self.entries_container)
        self.entries_container.setLayout(self.entries_layout)
        self.scroll_area.setWidget(self.entries_container)
        main_layout.addWidget(self.scroll_area)

        # Load script data from JSON
        json_data = self.load_script_data()

        # Build a mapping of script filename -> full path (by scanning the folder)
        script_path_map = self.find_script_paths(json_data)

        # For each JSON entry, create a composite widget:
        for entry in json_data:
            script_name = entry["Script"]
            if script_name not in script_path_map:
                continue  # skip if not found

            entry_widget = QWidget()
            entry_layout = QVBoxLayout(entry_widget)
            entry_layout.setContentsMargins(8, 8, 8, 8)
            entry_layout.setSpacing(5)

            # Launch button shows the App Name
            launch_button = QPushButton(entry["App Name"])
            launch_button.clicked.connect(lambda checked, sp=script_path_map[script_name]: self.launch_script(sp))
            launch_button.setToolTip(f"Launch {script_name}")
            entry_layout.addWidget(launch_button)

            # Below the button, display the rest of the information
            info_label = QLabel(
                f"<b>Script:</b> {entry['Script']}<br>"
                f"<b>Description:</b> {entry['Description']}<br>"
                f"<b>Author:</b> {entry['Author']}<br>"
                f"<b>Version:</b> {entry['Version']}"
            )
            info_label.setTextFormat(Qt.RichText)
            info_label.setWordWrap(True)
            entry_layout.addWidget(info_label)

            self.entries_layout.addWidget(entry_widget)

        # Transparency slider at the bottom
        slider_label = QLabel("Window Transparency:")
        main_layout.addWidget(slider_label)
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(20, 100)  # 20% to 100% opacity
        self.opacity_slider.setValue(100)
        self.opacity_slider.valueChanged.connect(self.adjust_opacity)
        main_layout.addWidget(self.opacity_slider)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def load_script_data(self):
        """
        Loads the script data from scripts.json and returns the parsed list of entries.
        """
        json_file = os.path.join(os.path.dirname(__file__), "scripts.json")
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load scripts.json:\n{e}")
            return []

    def find_script_paths(self, json_data):
        """
        Recursively scans the current folder (ignoring venv directories) for each 'Script'
        listed in json_data and returns a dict {script_filename: full_path}.
        """
        root_dir = os.path.dirname(os.path.abspath(__file__))
        needed_scripts = {entry["Script"] for entry in json_data}
        found_paths = {}
        ignored_dirs = {"venv", "env", ".venv"}

        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = [d for d in dirnames if d.lower() not in ignored_dirs]
            for filename in filenames:
                if filename in needed_scripts and filename.endswith(".py"):
                    found_paths[filename] = os.path.join(dirpath, filename)
        return found_paths

    def launch_script(self, script_path):
        """
        Launches the given Python script as a separate process.
        """
        try:
            subprocess.Popen([sys.executable, script_path])
            self.status_bar.showMessage(f"Launched {os.path.basename(script_path)}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch {script_path}\nError: {str(e)}")

    def adjust_opacity(self, value):
        """
        Adjusts the window opacity based on the slider value.
        """
        self.setWindowOpacity(value / 100.0)
        self.status_bar.showMessage(f"Window opacity set to {value}%", 2000)

    def apply_dark_theme(self):
        """
        Applies a QSS-based dark theme with a background of #1E1E1E, white text, and blue accent.
        """
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            QWidget {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #007ACC;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #005A9E;
            }
            QLabel {
                color: #FFFFFF;
                font-size: 10pt;
            }
            QScrollArea {
                background-color: #1E1E1E;
                border: none;
            }
            QSlider::groove:horizontal {
                border: 1px solid #444444;
                background: #444444;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #007ACC;
                border: 1px solid #007ACC;
                width: 18px;
                margin: -4px 0;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #007ACC;
                border: 1px solid #007ACC;
                height: 8px;
                border-radius: 4px;
            }
            QStatusBar {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
        """)

def main():
    app = QApplication(sys.argv)
    command_app = CommandApp()
    command_app.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
