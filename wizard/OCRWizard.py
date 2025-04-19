import os
import sys
import subprocess
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import pytesseract
import json
import time

# Path to the configuration file located in the application's root directory.
CONFIG_PATH = os.path.join(os.getcwd(), "config.json")
# Path to the application's log file for detailed logs.
LOG_FILE_PATH = os.path.join(os.getcwd(), "log.txt")

class OCRWizard:
    def __init__(self, parent):
        self.root = parent
        self.root.title("SLACKER IT Ai - OCR Setup Wizard")
        self.root.geometry("650x450")

        # Set the window icon from root/resources/slackerit.png
        try:
            icon = tk.PhotoImage(file=os.path.join("root", "resources", "slackerit.png"))
            self.root.iconphoto(False, icon)
        except Exception as e:
            print("Error setting icon:", e)

        # Use the "darkly" theme and apply a dark background.
        self.style = tb.Style(theme="darkly")
        self.apply_dark_style()

        # Limit for auto-search attempts.
        self.auto_search_attempts = 0
        self.max_auto_attempts = 3

        self.create_widgets()
        threading.Thread(target=self.check_tesseract, daemon=True).start()

    def apply_dark_style(self):
        """Force a dark style to match the app's look."""
        self.root.configure(bg="#1E1E1E")

    def create_widgets(self):
        # Title/status label at the top
        self.status_label = ttk.Label(
            self.root,
            text="Checking Tesseract OCR installation...",
            font=("Segoe UI", 14),
            foreground="#FFFFFF",
            background="#1E1E1E"
        )
        self.status_label.pack(pady=15)

        # Scrolled text for logs
        self.log_box = scrolledtext.ScrolledText(
            self.root,
            state='disabled',
            height=14,
            bg="#1E1E1E",
            fg="#FFFFFF",
            insertbackground="#FFFFFF",
            wrap=tk.WORD
        )
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Define color tags for the log_box.
        self.log_box.tag_config("green", foreground="#00FF00")
        self.log_box.tag_config("red", foreground="#FF0000")
        self.log_box.tag_config("blue", foreground="#00BFFF")

        # Action button (default: Exit)
        self.action_button = ttk.Button(
            self.root,
            text="Exit",
            command=self.root.quit,
            bootstyle="danger"
        )
        self.action_button.pack(pady=5)

        # Button for manual search; hidden by default.
        self.search_button = ttk.Button(
            self.root,
            text="Manual Search for Tesseract",
            command=self.manual_search,
            bootstyle="primary"
        )
        self.search_button.pack(pady=5)
        self.search_button.pack_forget()

    def pick_color_tag(self, message: str) -> str:
        """
        Decide which color tag to use for a given message.
        - If "❌", "fail", "error", or "not found" are in the text => red
        - Else if "✅", "found", "installed", "detected", or "success" => green
        - Otherwise => blue
        """
        lower_msg = message.lower()

        # Check "not found" and error terms first so they don't get mistaken for "found".
        if any(keyword in lower_msg for keyword in ["❌", "fail", "error", "not found"]):
            return "red"
        elif any(keyword in lower_msg for keyword in ["✅", "found", "installed", "detected", "success"]):
            return "green"
        return "blue"

    def log(self, message: str, level: int = 1):
        """
        Unified logging method.
          - Writes all messages (with timestamp and level) to LOG_FILE_PATH.
          - Displays messages in the GUI log_box without timestamps/level tags.
          - Color-codes each line using pick_color_tag.
        """
        # Write to log file (with timestamp and level).
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        log_file_message = f"[{timestamp}] [Level {level}] {message}\n"
        try:
            with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
                f.write(log_file_message)
        except Exception as e:
            self.display_in_gui(f"Error writing to log file: {str(e)}", "red")
            return

        # Display message in GUI without timestamp/level info.
        color_tag = self.pick_color_tag(message)
        self.display_in_gui(message, color_tag)

    def display_in_gui(self, plain_text: str, color_tag: str):
        """Insert a message into the ScrolledText using the given color tag."""
        self.log_box.config(state='normal')
        self.log_box.insert(tk.END, plain_text + "\n", color_tag)
        self.log_box.see(tk.END)
        self.log_box.config(state='disabled')

    def check_tesseract(self):
        self.log("Checking for Tesseract OCR in PATH...", level=1)
        try:
            result = subprocess.run(["tesseract", "-v"], capture_output=True, text=True)
            if result.returncode == 0 and "tesseract" in result.stdout.lower():
                # If Tesseract is found, the top line will be green because of the "✅" marker.
                self.log("✅ Tesseract OCR detected via PATH:", level=1)
                self.log(result.stdout.splitlines()[0], level=2)
                self.status_label.config(text="✅ Tesseract OCR is installed and detected.")
                self.action_button.config(text="Exit", command=self.root.quit, bootstyle="success")
                # Update config with current values.
                tessdata_dir = os.path.join(os.path.dirname("tesseract"), "tessdata")
                self.write_config({"tesseract_path": "tesseract", "tessdata_prefix": tessdata_dir})
                self.log("Updated config with Tesseract path from PATH search.", level=2)
                return
            else:
                raise Exception("Tesseract not detected via PATH")
        except Exception as e:
            self.log(f"❌ Tesseract not found in PATH: {str(e)}", level=1)
            if self.auto_search_attempts < self.max_auto_attempts:
                self.auto_search_attempts += 1
                self.log(f"Auto-search attempt {self.auto_search_attempts} of {self.max_auto_attempts}...", level=2)
                found = self.auto_search_tesseract()
                if found:
                    self.log(f"✅ Found Tesseract at: {found}", level=1)
                    tessdata_dir = os.path.join(os.path.dirname(found), "tessdata")
                    self.write_config({"tesseract_path": found, "tessdata_prefix": tessdata_dir})
                    pytesseract.pytesseract.tesseract_cmd = found
                    os.environ["TESSDATA_PREFIX"] = tessdata_dir
                    self.log(f"Set TESSDATA_PREFIX to: {tessdata_dir}", level=2)
                    folder = os.path.dirname(found)
                    if folder not in os.environ["PATH"]:
                        os.environ["PATH"] = folder + os.pathsep + os.environ["PATH"]
                        self.log(f"Added '{folder}' to PATH.", level=2)
                    threading.Thread(target=self.check_tesseract, daemon=True).start()
                    return
            self.log("❌ Could not locate Tesseract automatically after multiple attempts.", level=1)
            self.status_label.config(text="⚠️ Tesseract OCR is not installed or not found in PATH.")
            self.action_button.config(text="Download & Install Tesseract OCR", command=self.download_tesseract, bootstyle="warning")
            self.search_button.pack(pady=5)

    def auto_search_tesseract(self):
        """Searches common directories for tesseract.exe and returns the first valid path."""
        candidates = []
        common_paths = [
            os.path.join("C:\\", "Program Files", "Tesseract-OCR"),
            os.path.join("C:\\", "Program Files (x86)", "Tesseract-OCR")
        ]
        for path in common_paths:
            exe_path = os.path.join(path, "tesseract.exe")
            if os.path.exists(exe_path):
                candidates.append(exe_path)
                self.log(f"Found candidate in common path: {exe_path}", level=2)
        if candidates:
            return candidates[0]
        search_base = os.path.join("C:\\", "Program Files")
        for root, dirs, files in os.walk(search_base):
            if "tesseract.exe" in files:
                candidate = os.path.join(root, "tesseract.exe")
                self.log(f"Found candidate via deep search: {candidate}", level=2)
                return candidate
            if root.count(os.sep) - search_base.count(os.sep) >= 3:
                dirs[:] = []
        return None

    def manual_search(self):
        """Opens a window listing candidate folders for manual selection."""
        search_win = tk.Toplevel(self.root)
        search_win.title("Manual Search for Tesseract")
        search_win.geometry("500x300")
        search_win.configure(bg="#1E1E1E")

        lbl = ttk.Label(
            search_win,
            text="Select a folder containing tesseract.exe:",
            font=("Segoe UI", 11),
            background="#1E1E1E",
            foreground="#FFFFFF"
        )
        lbl.pack(pady=10)

        listbox = tk.Listbox(search_win, width=80, height=10, bg="#1E1E1E", fg="#FFFFFF")
        listbox.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        candidate_dirs = []
        for base in [os.path.join("C:\\", "Program Files"), os.path.join("C:\\", "Program Files (x86)")]:
            for root, dirs, files in os.walk(base):
                if "tesseract.exe" in files:
                    candidate_dirs.append(root)
                if root.count(os.sep) - base.count(os.sep) >= 3:
                    dirs[:] = []
        if candidate_dirs:
            for candidate in candidate_dirs:
                listbox.insert(tk.END, candidate)
            lbl.config(text="Select the folder containing tesseract.exe:")
        else:
            listbox.insert(tk.END, "No candidates found. Please select a folder manually.")
            lbl.config(text="No candidate installations found.")

        def on_select():
            selection = listbox.curselection()
            if selection:
                chosen = listbox.get(selection[0])
                exe_path = os.path.join(chosen, "tesseract.exe")
                if os.path.exists(exe_path):
                    pytesseract.pytesseract.tesseract_cmd = exe_path
                    tessdata_dir = os.path.join(os.path.dirname(exe_path), "tessdata")
                    self.log(f"✅ Tesseract executable set to: {exe_path}", level=1)
                    self.write_config({"tesseract_path": exe_path, "tessdata_prefix": tessdata_dir})
                    os.environ["TESSDATA_PREFIX"] = tessdata_dir
                    self.log(f"Set TESSDATA_PREFIX to: {tessdata_dir}", level=2)
                    search_win.destroy()
                    threading.Thread(target=self.check_tesseract, daemon=True).start()
                else:
                    messagebox.showerror("Error", "Selected folder does not contain tesseract.exe.")
            else:
                messagebox.showinfo("Selection", "Please select a folder from the list.")
        select_btn = ttk.Button(search_win, text="Select", command=on_select, bootstyle="primary")
        select_btn.pack(pady=10)

    def download_tesseract(self):
        webbrowser.open("https://github.com/tesseract-ocr/tesseract/releases")
        messagebox.showinfo(
            "Download Tesseract OCR",
            "Your browser will open the Tesseract OCR GitHub releases page.\n"
            "Download the installer appropriate for your system.\n\n"
            "After downloading, click OK and then use the manual search to locate Tesseract."
        )
        self.manual_search()

    def write_config(self, data):
        """Write the given data to the config.json file."""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    config = json.load(f)
            else:
                config = {}
            config.update(data)
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
            self.log("✅ Configuration updated.", level=1)
        except Exception as e:
            self.log(f"❌ Failed to update config: {str(e)}", level=1)

if __name__ == "__main__":
    root = tb.Window(themename="darkly")
    app = OCRWizard(root)
    root.mainloop()
