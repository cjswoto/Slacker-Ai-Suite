import sys
import os
import json
import subprocess
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QGridLayout,
    QScrollArea, QSlider, QLabel, QStatusBar, QMessageBox, QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QGuiApplication

class CommandApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set static view mode.
        self.view_mode = "Dashboard"  # Always Dashboard

        # Load static script list from the menuscripts folder.
        self.json_data = []      # Loaded script list data
        self.script_path_map = {}  # Mapping: {script filename: full path}
        self.entry_widgets = []  # List of created entry widgets
        self.load_static_script_list()

        # Set window title and size to 800x600 (do not start maximized).
        self.setWindowTitle("SLACKER IT Ai")
        self.resize(800, 600)

        # Apply dark theme.
        self.apply_dark_theme()

        # Main widget and layout.
        main_widget = QWidget()
        self.main_layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # Create status bar.
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Create scroll area for script entries.
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.entries_container = QWidget()
        self.entries_layout = None  # Will be set in update_entries_layout
        self.scroll_area.setWidget(self.entries_container)
        self.main_layout.addWidget(self.scroll_area)

        # Build entry widgets from the loaded JSON.
        for entry in self.json_data:
            widget = self.create_entry_widget(entry)
            self.entry_widgets.append(widget)
        self.update_entries_layout()

        # Transparency slider.
        slider_label = QLabel("Window Transparency:")
        self.main_layout.addWidget(slider_label)
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(20, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.valueChanged.connect(self.adjust_opacity)
        self.main_layout.addWidget(self.opacity_slider)

    def load_static_script_list(self):
        """Loads 'scripts_default.json' from the 'menuscripts' folder (in the main project directory)."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        script_list_path = os.path.join(base_dir, "menuscripts", "scripts_default.json")
        try:
            with open(script_list_path, "r", encoding="utf-8") as f:
                self.json_data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load scripts_default.json from menuscripts:\n{str(e)}")
            sys.exit(1)
        self.script_path_map = self.find_script_paths(self.json_data)

    def find_script_paths(self, json_data):
        """Recursively scans the project folder (ignoring virtual environment directories) for each 'Script' and returns a dict."""
        root_dir = os.path.dirname(os.path.abspath(__file__))
        needed_scripts = {entry.get("Script", "") for entry in json_data}
        found_paths = {}
        ignored_dirs = {"venv", "env", ".venv"}
        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = [d for d in dirnames if d.lower() not in ignored_dirs]
            for filename in filenames:
                if filename in needed_scripts and filename.endswith(".py"):
                    found_paths[filename] = os.path.join(dirpath, filename)
        return found_paths

    def create_entry_widget(self, entry):
        """Creates a widget for a given JSON entry with a launch button and info label."""
        script_name = entry.get("Script", "")
        script_path = self.script_path_map.get(script_name)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)

        launch_button = QPushButton(entry.get("App Name", "Unnamed App"))
        if script_path:
            launch_button.clicked.connect(lambda checked, sp=script_path: self.launch_script(sp))
            launch_button.setToolTip(f"Launch {script_name}")
        else:
            launch_button.setEnabled(False)
            launch_button.setToolTip(f"Script file '{script_name}' not found")
        layout.addWidget(launch_button)

        info_label = QLabel(
            f"<b>Script:</b> {entry.get('Script', '')}<br>"
            f"<b>Description:</b> {entry.get('Description', '')}<br>"
            f"<b>Author:</b> {entry.get('Author', '')}<br>"
            f"<b>Version:</b> {entry.get('Version', '')}"
        )
        info_label.setTextFormat(Qt.RichText)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        return widget

    def update_entries_layout(self):
        """Displays all entry widgets in a static dashboard view (grid layout with 2 columns)."""
        if self.entries_container.layout() is not None:
            old_layout = self.entries_container.layout()
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
            old_layout.deleteLater()
        new_layout = QGridLayout()
        cols = 2
        for index, widget in enumerate(self.entry_widgets):
            row = index // cols
            col = index % cols
            new_layout.addWidget(widget, row, col)
        self.entries_container.setLayout(new_layout)

    def launch_script(self, script_path):
        try:
            subprocess.Popen([sys.executable, script_path])
            self.status_bar.showMessage(f"Launched {os.path.basename(script_path)}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch {script_path}\nError: {str(e)}")

    def adjust_opacity(self, value):
        self.setWindowOpacity(value / 100.0)
        self.status_bar.showMessage(f"Window opacity set to {value}%", 2000)

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #1E1E1E; color: #FFFFFF; }
            QWidget { background-color: #1E1E1E; color: #FFFFFF; }
            QPushButton {
                background-color: #007ACC; color: #FFFFFF;
                border: none; border-radius: 4px; padding: 8px 12px; font-size: 11pt;
            }
            QPushButton:hover { background-color: #005A9E; }
            QLabel { color: #FFFFFF; font-size: 10pt; }
            QScrollArea { background-color: #1E1E1E; border: none; }
            QSlider::groove:horizontal { border: 1px solid #444444; background: #444444; height: 8px; border-radius: 4px; }
            QSlider::handle:horizontal { background: #007ACC; border: 1px solid #007ACC; width: 18px; margin: -4px 0; border-radius: 3px; }
            QSlider::sub-page:horizontal { background: #007ACC; border: 1px solid #007ACC; height: 8px; border-radius: 4px; }
            QStatusBar { background-color: #1E1E1E; color: #FFFFFF; }
        """)

def main():
    app = QApplication(sys.argv)
    command_app = CommandApp()
    command_app.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
