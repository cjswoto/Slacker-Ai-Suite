import sys
import os
import json
import subprocess
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QScrollArea,
    QSlider, QLabel, QStatusBar, QMessageBox, QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QGuiApplication

# Inline JSON data (combined from scripts.json)
SCRIPTS_JSON = """
[
  {
    "App Name": "CUDA Installation Wizard",
    "Script": "CUDAWizard.py",
    "Description": "Acts as a CUDA Installation Wizard. Checks for CUDA, and if not detected, guides the user through downloading and installing the CUDA Toolkit.",
    "Author": "CJS",
    "Version": "v1.0"
  },
  {
    "App Name": "Ollama Setup Wizard",
    "Script": "OllamaWizard.py",
    "Description": "Implements a setup wizard for Ollama, a local AI inference platform. Checks system prerequisites, verifies installation and running status, and guides the user through model downloads and configuration.",
    "Author": "CJS",
    "Version": "v1.0"
  },
  {
    "App Name": "Ollama Data Preparation",
    "Script": "ollamadataprep.py",
    "Description": "A modern GUI app for converting raw document data into structured datasets suitable for training. Supports multiple file types and exports the processed data in JSON Lines format.",
    "Author": "CJS",
    "Version": "v1.0"
  },
  {
    "App Name": "PDF to Training Dataset",
    "Script": "cuttrainfile.py",
    "Description": "Offers a GUI for generating a training dataset from a PDF document by extracting text and prompting an AI model, then saving the generated dataset as JSON.",
    "Author": "CJS",
    "Version": "v1.0"
  },
  {
    "App Name": "Ollama Model Trainer",
    "Script": "ollamatrainer.py",
    "Description": "Provides a production-grade GUI for fine-tuning open-source language models using quantization and LoRA techniques. Leverages PyTorch and Hugging Face Transformers for model training and conversion for deployment with Ollama.",
    "Author": "CJS",
    "Version": "v1.0"
  },
  {
    "App Name": "Local KB Manager",
    "Script": "kb_gui.py",
    "Description": "Implements a tkinter-based GUI for managing a local knowledge base. Users can add files, view document metadata, and remove files, triggering re-indexing as needed.",
    "Author": "CJS",
    "Version": "v1.0"
  },
  {
    "App Name": "PDF Image Extractor",
    "Script": "PDFMaster.py",
    "Description": "Enables users to extract images from PDF documents using PyMuPDF. Offers PDF preview and options for extracting embedded images or saving full-page snapshots, displayed in a scrollable interface.",
    "Author": "CJS",
    "Version": "v1.0"
  },
  {
    "App Name": "OllamaChat - Main GUI",
    "Script": "chat_gui_main.py",
    "Description": "Serves as the main chat GUI for the OllamaChat application. Integrates the chat interface, settings panel, and session panel while managing background tasks like model refreshing and server connection checks.",
    "Author": "CJS",
    "Version": "v1.0"
  }
]
"""


class CommandApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Get screen geometry and calculate window dimensions/position:
        screen_rect = QGuiApplication.primaryScreen().availableGeometry()
        screen_width = screen_rect.width()
        screen_height = screen_rect.height()

        window_width = screen_width // 8
        window_height = int(screen_height * 0.9)  # 90% of screen height
        x = screen_width - window_width  # Snapped to the right edge
        y = int(screen_height * 0.05)  # Start slightly below top to keep header visible

        self.setGeometry(x, y, window_width, window_height)
        self.setWindowTitle("SLACKER IT - AI Suite")
        self.apply_dark_theme()

        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # Banner removed as requested.

        # Scroll area for JSON entries
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.entries_container = QWidget()
        self.entries_layout = QVBoxLayout(self.entries_container)
        self.entries_container.setLayout(self.entries_layout)
        self.scroll_area.setWidget(self.entries_container)
        main_layout.addWidget(self.scroll_area)

        # Load script data from inline JSON
        json_data = self.load_script_data()

        # Build a mapping of script filename -> full path (by scanning the folder)
        script_path_map = self.find_script_paths(json_data)

        # For each JSON entry, create a composite widget:
        for entry in json_data:
            script_name = entry.get("Script", "")
            script_path = script_path_map.get(script_name)

            entry_widget = QWidget()
            entry_layout = QVBoxLayout(entry_widget)
            entry_layout.setContentsMargins(8, 8, 8, 8)
            entry_layout.setSpacing(5)

            # Launch button shows the App Name. If the script file isn't found, disable the button.
            launch_button = QPushButton(entry.get("App Name", "Unnamed App"))
            if script_path:
                launch_button.clicked.connect(lambda checked, sp=script_path: self.launch_script(sp))
                launch_button.setToolTip(f"Launch {script_name}")
            else:
                launch_button.setEnabled(False)
                launch_button.setToolTip(f"Script file '{script_name}' not found")
            entry_layout.addWidget(launch_button)

            # Display additional information below the button
            info_label = QLabel(
                f"<b>Script:</b> {entry.get('Script', '')}<br>"
                f"<b>Description:</b> {entry.get('Description', '')}<br>"
                f"<b>Author:</b> {entry.get('Author', '')}<br>"
                f"<b>Version:</b> {entry.get('Version', '')}"
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
        """Parses and returns the inline JSON data."""
        try:
            data = json.loads(SCRIPTS_JSON)
            return data
        except Exception as e:
            error_message = f"Failed to parse inline JSON data:\n{e}"
            print(error_message)  # Debug output to the console
            QMessageBox.critical(self, "Error", error_message)
            return []

    def find_script_paths(self, json_data):
        """
        Recursively scans the current folder (ignoring venv directories) for each 'Script'
        listed in json_data and returns a dict {script_filename: full_path}.
        """
        # In frozen mode, __file__ points to a temporary folder containing bundled files.
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

    def launch_script(self, script_path):
        """Launches the given Python script as a separate process."""
        try:
            subprocess.Popen([sys.executable, script_path])
            self.status_bar.showMessage(f"Launched {os.path.basename(script_path)}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch {script_path}\nError: {str(e)}")

    def adjust_opacity(self, value):
        """Adjusts the window opacity based on the slider value."""
        self.setWindowOpacity(value / 100.0)
        self.status_bar.showMessage(f"Window opacity set to {value}%", 2000)

    def apply_dark_theme(self):
        """Applies a QSS-based dark theme with a background of #1E1E1E, white text, and blue accent."""
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
