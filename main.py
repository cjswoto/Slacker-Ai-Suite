import sys
import os
import json
import subprocess
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QScrollArea, QSlider, QLabel, QStatusBar, QMessageBox, QPushButton, QComboBox, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QGuiApplication

class CommandApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Define attributes early.
        self.config = {}                # Configuration data
        self.scriptlists_folder = ""    # Folder where JSON script lists are stored
        self.json_data = []             # Loaded script list data
        self.script_path_map = {}       # Mapping: {script filename: full path}
        self.entry_widgets = []         # List of created entry widgets
        self.view_mode = "List"         # Default view mode
        self.status_bar = None          # Will be created below

        # Load configuration and determine folder for script lists.
        self.load_config()
        self.scriptlists_folder = self.get_scriptlists_folder()

        # Setup window dimensions.
        screen_rect = QGuiApplication.primaryScreen().availableGeometry()
        screen_width = screen_rect.width()
        screen_height = screen_rect.height()
        window_width = screen_width // 8
        window_height = int(screen_height * 0.9)
        x = screen_width - window_width
        y = int(screen_height * 0.05)
        self.setGeometry(x, y, window_width, window_height)
        self.setWindowTitle("SLACKER IT - AI Suite")
        self.apply_dark_theme()

        # Main widget and layout.
        main_widget = QWidget()
        self.main_layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # Create the status bar first.
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Header layout: view mode selector and script list selector.
        header_layout = QHBoxLayout()
        view_mode_label = QLabel("View Mode:")
        header_layout.addWidget(view_mode_label)
        self.view_mode_combo = QComboBox()
        self.view_mode_combo.addItems(["List", "Dashboard"])
        self.view_mode_combo.currentTextChanged.connect(self.change_view_mode)
        header_layout.addWidget(self.view_mode_combo)

        script_list_label = QLabel("Script List:")
        header_layout.addWidget(script_list_label)
        self.script_list_combo = QComboBox()
        self.populate_script_list_combo()
        # Use the 'activated' signal so the list is reloaded only on user selection.
        self.script_list_combo.activated[str].connect(self.load_selected_script_list)
        header_layout.addWidget(self.script_list_combo)
        header_layout.addStretch()
        self.main_layout.addLayout(header_layout)

        # Scroll area for script entries.
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.entries_container = QWidget()
        self.entries_layout = None  # Will be set by update_entries_layout
        self.scroll_area.setWidget(self.entries_container)
        self.main_layout.addWidget(self.scroll_area)

        # Load initial script list from the combo box's current selection.
        current_list = self.script_list_combo.currentText()
        self.json_data = self.load_selected_script_list(current_list)
        self.script_path_map = self.find_script_paths(self.json_data)
        self.entry_widgets = []
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

    # ------------------ CONFIGURATION METHODS ------------------
    def load_config(self):
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            except Exception as e:
                QMessageBox.warning(self, "Warning", f"Failed to load config.json:\n{str(e)}")
                self.config = {}
        else:
            self.config = {}

    def save_config(self):
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Failed to save config.json:\n{str(e)}")

    def get_scriptlists_folder(self):
        default_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "apps", "scriptlists")
        if "scriptlists_folder" in self.config and os.path.isdir(self.config["scriptlists_folder"]):
            return self.config["scriptlists_folder"]
        elif os.path.isdir(default_folder):
            return default_folder
        else:
            selected_folder = QFileDialog.getExistingDirectory(self, "Select Script Lists Folder")
            if selected_folder:
                self.config["scriptlists_folder"] = selected_folder
                self.save_config()
                return selected_folder
            else:
                QMessageBox.critical(self, "Error", "No folder selected. Exiting application.")
                sys.exit(1)

    # ------------------ SCRIPT LIST LOADING ------------------
    def populate_script_list_combo(self):
        files = []
        if os.path.isdir(self.scriptlists_folder):
            for file in os.listdir(self.scriptlists_folder):
                if file.endswith(".json"):
                    files.append(file)
        if not files:
            QMessageBox.information(self, "Info", "No script list files found. Defaulting to 'scripts_default.json'.")
            files = ["scripts_default.json"]
        self.script_list_combo.clear()
        self.script_list_combo.addItems(files)

    def load_selected_script_list(self, filename):
        if not filename:
            return []
        folder = self.scriptlists_folder
        file_path = os.path.join(folder, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.status_bar.showMessage(f"Loaded script list from {filename}", 3000)
            # Rebuild entry widgets.
            self.json_data = data
            self.script_path_map = self.find_script_paths(self.json_data)
            self.entry_widgets = []
            for entry in self.json_data:
                widget = self.create_entry_widget(entry)
                self.entry_widgets.append(widget)
            self.update_entries_layout()
            return data
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load {filename}:\n{str(e)}")
            self.status_bar.showMessage(f"Error loading {filename}", 3000)
            return []

    def find_script_paths(self, json_data):
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

    # ------------------ ENTRY WIDGETS & LAYOUT ------------------
    def create_entry_widget(self, entry):
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
        if self.entries_container.layout() is not None:
            old_layout = self.entries_container.layout()
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
            old_layout.deleteLater()
        if self.view_mode == "List":
            new_layout = QVBoxLayout()
            for widget in self.entry_widgets:
                new_layout.addWidget(widget)
        elif self.view_mode == "Dashboard":
            new_layout = QGridLayout()
            cols = 2
            for index, widget in enumerate(self.entry_widgets):
                row = index // cols
                col = index % cols
                new_layout.addWidget(widget, row, col)
        else:
            new_layout = QVBoxLayout()
        self.entries_container.setLayout(new_layout)

    def change_view_mode(self, mode):
        self.view_mode = mode
        self.update_entries_layout()
        self.status_bar.showMessage(f"Switched to {mode} view", 2000)

    def launch_script(self, script_path):
        try:
            subprocess.Popen([sys.executable, script_path])
            self.status_bar.showMessage(f"Launched {os.path.basename(script_path)}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch {script_path}\nError: {str(e)}")

    # ------------------ OPACITY & THEME ------------------
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
