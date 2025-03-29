import os
import sys
import platform
import subprocess
import threading
import tempfile
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import json
import time
from ttkbootstrap import Style
from PIL import Image, ImageTk
from io import BytesIO


class OllamaSetupWizard:
    def __init__(self, parent):
        # If parent is a root window (has title), use it; otherwise, create an internal frame.
        if hasattr(parent, "title"):
            parent.title("Ollama Setup")
            self.root = parent
        else:
            self.root = tk.Frame(parent)
            self.root.pack(fill=tk.BOTH, expand=True)

        # Apply a modern theme
        self.style = Style(theme="darkly")

        # Variables
        self.system = platform.system()
        self.ollama_installed = False
        self.ollama_running = False
        self.featured_models = [
            {"name": "llama3", "size": "~4GB", "description": "Meta's Llama3 model, good for general use"},
            {"name": "phi3:latest", "size": "~4GB",
             "description": "Microsoft's Phi-3 model, very good instruction following"},
            {"name": "mistral", "size": "~4GB", "description": "Mistral 7B model, excellent performance for its size"},
            {"name": "codellama", "size": "~4GB", "description": "Optimized for code generation and completion"},
            {"name": "vicuna", "size": "~4GB",
             "description": "Fine-tuned LLaMA, good for chat and instruction following"},
            {"name": "llava", "size": "~4.5GB", "description": "Multimodal model that can analyze images"},
            {"name": "gemma:2b", "size": "~1.5GB", "description": "Google's Gemma model, lightweight and efficient"},
            {"name": "falcon:7b", "size": "~4GB", "description": "TII's Falcon model, powerful and efficient"}
        ]

        # Create a main scrollable frame so the entire setup is viewable if it doesn’t fit on screen.
        self.main_canvas = tk.Canvas(self.root, borderwidth=0)
        self.v_scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.main_canvas.yview)
        self.main_frame = ttk.Frame(self.main_canvas, padding=20)
        self.main_frame.bind(
            "<Configure>",
            lambda event: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )

        # ADDED: store create_window in self.main_window
        self.main_window = self.main_canvas.create_window((0, 0), window=self.main_frame, anchor="nw")

        self.main_canvas.configure(yscrollcommand=self.v_scrollbar.set)
        self.main_canvas.pack(side="left", fill="both", expand=True)
        self.v_scrollbar.pack(side="right", fill="y")

        # ADDED: define on_canvas_resize
        def on_canvas_resize(event):
            # Force main_frame to match the canvas width
            self.main_canvas.itemconfig(self.main_window, width=event.width)

        # ADDED: bind <Configure>
        self.main_canvas.bind("<Configure>", on_canvas_resize)

        # Build the one-screen UI sections.
        self.build_ui()

        # Automatically start prerequisites check in background.
        threading.Thread(target=self.check_prerequisites, daemon=True).start()

    def build_ui(self):
        # ----- Welcome Section -----
        welcome_frame = ttk.LabelFrame(self.main_frame, text="Welcome", padding=10)
        welcome_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        header = ttk.Label(welcome_frame, text="Welcome to the Ollama Setup", font=("Segoe UI", 18, "bold"))
        header.pack(pady=(0, 10))
        desc = ttk.Label(welcome_frame, text=(
            "This process will guide you through setting up Ollama on your system and downloading models for local AI inference.\n\n"
            "Ollama allows you to run large language models locally on your computer, providing privacy and offline access."
        ), font=("Segoe UI", 11), wraplength=2000, justify="center")
        desc.pack()
        system_label = ttk.Label(welcome_frame, text=f"Detected System: {self.system}", font=("Segoe UI", 11))
        system_label.pack(anchor=tk.W, pady=(10, 0))

        # ----- Prerequisites Section -----
        prereq_frame = ttk.LabelFrame(self.main_frame, text="System Prerequisites", padding=10)
        prereq_frame.pack(fill=tk.BOTH, pady=5)
        self.prereq_step_label = ttk.Label(prereq_frame, text="Checking prerequisites...", font=("Segoe UI", 11))
        self.prereq_step_label.pack(pady=(0, 5))
        self.prereq_log = scrolledtext.ScrolledText(prereq_frame, height=10, font=("Consolas", 10),
                                                    bg="#2b2b2b", fg="#ffffff", wrap=tk.WORD)
        self.prereq_log.pack(fill=tk.BOTH, expand=True)

        # ----- Installation Section -----
        install_frame = ttk.LabelFrame(self.main_frame, text="Installation Status", padding=10)
        install_frame.pack(fill=tk.BOTH, pady=5)
        self.install_step_label = ttk.Label(install_frame, text="Reviewing installation status...",
                                            font=("Segoe UI", 11))
        self.install_step_label.pack(pady=(0, 5))
        self.install_status_label = ttk.Label(install_frame, text="", font=("Segoe UI", 11), wraplength=700)
        self.install_status_label.pack(pady=(0, 5))
        # A progress bar for installation and service start actions.
        self.install_progress_bar = ttk.Progressbar(install_frame, mode="indeterminate", length=400)
        # A button to trigger installation or starting service when needed.
        self.install_action_button = ttk.Button(install_frame, text="", command=self.install_or_start)
        self.install_action_button.pack(pady=(5, 0))

        # Store install_frame so references work
        self.install_frame = install_frame

        # ----- Model Download Section -----
        model_frame = ttk.LabelFrame(self.main_frame, text="Model Download", padding=10)
        model_frame.pack(fill=tk.BOTH, pady=5)
        self.model_step_label = ttk.Label(model_frame, text="Select models to download", font=("Segoe UI", 11))
        self.model_step_label.pack(pady=(0, 5))

        checkbox_container = ttk.Frame(model_frame)
        checkbox_container.pack(fill=tk.BOTH, expand=True)

        model_canvas = tk.Canvas(checkbox_container, bg="#2b2b2b", highlightthickness=0)
        model_scrollbar = ttk.Scrollbar(checkbox_container, orient="vertical", command=model_canvas.yview)
        self.model_scrollable_frame = ttk.Frame(model_canvas)
        self.model_scrollable_frame.bind(
            "<Configure>",
            lambda e: model_canvas.configure(scrollregion=model_canvas.bbox("all"))
        )
        model_canvas.create_window((0, 0), window=self.model_scrollable_frame, anchor="nw")
        model_canvas.configure(yscrollcommand=model_scrollbar.set)
        model_canvas.pack(side="left", fill="both", expand=True)
        model_scrollbar.pack(side="right", fill="y")

        self.model_vars = {}
        self.model_checkbuttons = {}
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                downloaded_models = [model["name"] for model in response.json().get("models", [])]
            else:
                downloaded_models = []
        except Exception:
            downloaded_models = []

        for model in self.featured_models:
            frame = ttk.Frame(self.model_scrollable_frame)
            frame.pack(fill=tk.X, pady=5)
            is_downloaded = any(model["name"].split(":")[0] in m for m in downloaded_models)
            self.model_vars[model["name"]] = tk.BooleanVar(value=False)
            checkbox = ttk.Checkbutton(frame, text=f"{model['name']} ({model['size']})",
                                       variable=self.model_vars[model["name"]],
                                       state=tk.DISABLED if is_downloaded else tk.NORMAL)
            checkbox.pack(side=tk.LEFT, padx=5)
            self.model_checkbuttons[model["name"]] = checkbox
            if is_downloaded:
                status = ttk.Label(frame, text="✅ Already downloaded", foreground="green")
                status.pack(side=tk.LEFT, padx=5)
            desc = ttk.Label(frame, text=model["description"], wraplength=500)
            desc.pack(side=tk.LEFT, padx=10)

        custom_frame = ttk.LabelFrame(self.model_scrollable_frame, text="Custom Model", padding=10)
        custom_frame.pack(fill=tk.X, pady=10)
        ttk.Label(custom_frame, text="Model name:").pack(side=tk.LEFT, padx=5)
        self.custom_model_entry = ttk.Entry(custom_frame, width=30)
        self.custom_model_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(custom_frame, text="(e.g., orca-mini:3b, codegemma:7b)").pack(side=tk.LEFT, padx=5)

        self.model_log = scrolledtext.ScrolledText(model_frame, height=6, font=("Consolas", 10),
                                                   bg="#2b2b2b", fg="#ffffff", wrap=tk.WORD)
        self.model_log.pack(fill=tk.BOTH, expand=True, pady=10)

        self.download_button = ttk.Button(model_frame, text="Download Selected Models",
                                          command=self.download_models, style="primary.TButton", width=25)
        self.download_button.pack(pady=5)

        # ----- Completion Section -----
        self.completion_frame = ttk.LabelFrame(self.main_frame, text="Setup Completion", padding=10)
        self.completion_frame.pack(fill=tk.BOTH, pady=5)
        self.completion_msg = ttk.Label(self.completion_frame, text="", font=("Segoe UI", 11),
                                        wraplength=700, justify="center")
        self.completion_msg.pack(pady=5)

    # --- Helper log/update functions for each section ---
    def log_prereq(self, message):
        self.prereq_log.insert(tk.END, message + "\n")
        self.prereq_log.see(tk.END)

    def update_prereq_step(self, text):
        self.prereq_step_label.config(text=text)

    def update_install_step(self, text):
        self.install_step_label.config(text=text)

    def log_install(self, message):
        current = self.install_status_label.cget("text")
        self.install_status_label.config(text=current + message + "\n")

    def append_model_log(self, message):
        self.model_log.insert(tk.END, message + "\n")
        self.model_log.see(tk.END)

    # --- Prerequisites Check ---
    def check_prerequisites(self):
        self.update_prereq_step("Checking CPU architecture")
        arch = platform.machine().lower()
        self.log_prereq(f"CPU Architecture: {arch}")
        if arch not in ('x86_64', 'amd64', 'arm64'):
            self.log_prereq("❌ Ollama requires a 64-bit processor (x86_64/amd64 or arm64)")
            self.update_prereq_step("Incompatible CPU architecture detected")
            return
        self.log_prereq("✅ Compatible CPU architecture detected")

        self.update_prereq_step("Checking system RAM")
        try:
            if self.system == "Windows":
                import ctypes
                kernel32 = ctypes.windll.kernel32
                c_ulonglong = ctypes.c_ulonglong

                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ('dwLength', ctypes.c_ulong),
                        ('dwMemoryLoad', ctypes.c_ulong),
                        ('ullTotalPhys', c_ulonglong),
                        ('ullAvailPhys', c_ulonglong),
                        ('ullTotalPageFile', c_ulonglong),
                        ('ullAvailPageFile', c_ulonglong),
                        ('ullTotalVirtual', c_ulonglong),
                        ('ullAvailVirtual', c_ulonglong),
                        ('ullAvailExtendedVirtual', c_ulonglong),
                    ]

                memoryStatus = MEMORYSTATUSEX()
                memoryStatus.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                kernel32.GlobalMemoryStatusEx(ctypes.byref(memoryStatus))
                ram_gb = memoryStatus.ullTotalPhys / (1024 ** 3)
            elif self.system == "Linux":
                with open('/proc/meminfo', 'r') as f:
                    mem_info = f.read()
                total_mem = int(
                    [line for line in mem_info.split('\n') if 'MemTotal' in line][0].split(':')[1].strip().split(' ')[0]
                ) / (1024 ** 2)
                ram_gb = total_mem
            elif self.system == "Darwin":
                output = subprocess.check_output(['sysctl', 'hw.memsize']).decode().strip()
                ram_bytes = int(output.split(' ')[1])
                ram_gb = ram_bytes / (1024 ** 3)
            self.log_prereq(f"System RAM: {ram_gb:.2f} GB")
            if ram_gb < 8:
                self.log_prereq("⚠️ Warning: Ollama recommends at least 8GB of RAM for optimal performance")
            else:
                self.log_prereq("✅ Sufficient RAM available")
        except Exception as e:
            self.log_prereq(f"⚠️ Could not determine RAM size: {str(e)}")

        self.update_prereq_step("Checking free disk space")
        try:
            if self.system == "Windows":
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p("C:\\"), None, None,
                                                           ctypes.pointer(free_bytes))
                free_gb = free_bytes.value / (1024 ** 3)
            else:
                stats = os.statvfs(os.path.expanduser("~"))
                free_gb = (stats.f_frsize * stats.f_bavail) / (1024 ** 3)
            self.log_prereq(f"Free disk space: {free_gb:.2f} GB")
            if free_gb < 10:
                self.log_prereq("⚠️ Warning: Less than 10GB free space available. Models typically require 4-8GB each")
            else:
                self.log_prereq("✅ Sufficient disk space available")
        except Exception as e:
            self.log_prereq(f"⚠️ Could not determine free disk space: {str(e)}")

        self.update_prereq_step("Verifying Ollama installation")
        self.check_ollama_installation()

        self.update_prereq_step("Prerequisites check completed")
        self.install_or_start()

    def check_ollama_installation(self):
        try:
            if self.system == "Windows":
                ollama_path = os.path.expanduser("~\\AppData\\Local\\Programs\\Ollama\\ollama.exe")
                self.ollama_installed = os.path.exists(ollama_path)
                if self.ollama_installed:
                    self.log_prereq(f"✅ Ollama found at: {ollama_path}")
                else:
                    self.log_prereq("Ollama not found in expected location")
            else:
                result = subprocess.run(["which", "ollama"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.ollama_installed = (result.returncode == 0)
                if self.ollama_installed:
                    self.log_prereq(f"✅ Ollama found at: {result.stdout.decode().strip()}")
                else:
                    self.log_prereq("Ollama not found in PATH")

            if self.ollama_installed:
                self.check_ollama_running()
        except Exception as e:
            self.log_prereq(f"⚠️ Error checking Ollama installation: {str(e)}")
            self.ollama_installed = False

    def check_ollama_running(self):
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            self.ollama_running = (response.status_code == 200)
            if self.ollama_running:
                self.log_prereq("✅ Ollama service is running")
            else:
                self.log_prereq("⚠️ Ollama service is not running")
        except Exception:
            self.log_prereq("⚠️ Ollama service is not running")
            self.ollama_running = False

    def install_or_start(self):
        # In this one-screen design the installation section shows an action button.
        # Set its text and command based on the current status.
        if not self.ollama_installed:
            self.install_action_button.config(text="Install Ollama", command=self.install_ollama)
        elif not self.ollama_running:
            self.install_action_button.config(text="Start Ollama", command=self.start_ollama)
        else:
            self.install_action_button.config(text="Installed and Running", state=tk.DISABLED)

    # ----- Installation / Service Start Methods -----
    def install_ollama(self):
        self.install_action_button.config(state=tk.DISABLED)
        self.progress_label = ttk.Label(self.install_frame, text="Downloading Ollama installer...",
                                        font=("Segoe UI", 10))
        self.progress_label.pack(pady=5)
        self.install_progress_bar.pack(fill=tk.X, pady=5)
        self.install_progress_bar.start()
        self.update_install_step("Starting Ollama installation")

        threading.Thread(target=self._install_ollama, daemon=True).start()

    def _install_ollama(self):
        try:
            if self.system == "Windows":
                self.update_install_step("Downloading Ollama for Windows")
                self.log_install("Downloading Ollama for Windows...")
                installer_url = "https://ollama.com/download/windows"
                response = requests.get(installer_url, stream=True)
                if response.status_code != 200:
                    self.log_install(f"❌ Failed to download: HTTP {response.status_code}")
                    return
                installer_path = os.path.join(tempfile.gettempdir(), "ollama_installer.exe")
                with open(installer_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                self.log_install(f"✅ Downloaded installer to: {installer_path}")
                self.update_install_step("Installer downloaded, launching installer")
                self.progress_label.config(text="Running installer...\nFollow the on-screen instructions.")
                subprocess.Popen([installer_path])
                self.log_install("🚀 Launched Ollama installer. Please complete the installation process.")
                messagebox.showinfo(
                    "Installation in Progress",
                    "The Ollama installer has been launched.\n\n"
                    "Please follow the on-screen instructions to complete installation.\n\n"
                    "When installation is complete, click OK to continue the setup."
                )
                self.log_install("Verifying installation after installer completion...")
                self.check_ollama_installation()
                if self.ollama_installed:
                    self.log_install("✅ Ollama has been successfully installed!")
                    if not self.ollama_running:
                        self.log_install("Starting Ollama service...")
                        self.start_ollama()
                else:
                    self.log_install("⚠️ Ollama installation could not be verified. Please try manually.")
            elif self.system == "Darwin":
                self.update_install_step("Opening Ollama download page for macOS")
                self.log_install("Downloading Ollama for macOS...")
                installer_url = "https://ollama.com/download/mac"
                webbrowser.open(installer_url)
                messagebox.showinfo(
                    "Installation in Progress",
                    "The Ollama download has started in your browser.\n\n"
                    "Please follow these steps:\n"
                    "1. Complete the download\n"
                    "2. Open the downloaded .dmg file\n"
                    "3. Drag Ollama to your Applications folder\n"
                    "4. Open Ollama from Applications\n\n"
                    "When installation is complete, click OK to continue the setup."
                )
                self.check_ollama_installation()
            elif self.system == "Linux":
                self.update_install_step("Installing Ollama on Linux")
                self.log_install("Installing Ollama for Linux...")
                install_command = 'curl -fsSL https://ollama.com/install.sh | sh'
                self.log_install(f"Running: {install_command}")
                process = subprocess.Popen(
                    install_command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                for line in process.stdout:
                    self.log_install(line.strip())
                process.wait()
                if process.returncode == 0:
                    self.log_install("✅ Ollama has been successfully installed!")
                    self.ollama_installed = True
                    self.start_ollama()
                else:
                    for line in process.stderr:
                        self.log_install(f"❌ {line.strip()}")
                    self.log_install("❌ Installation failed. Please try manually.")
        except Exception as e:
            self.log_install(f"❌ Error during installation: {str(e)}")
        finally:
            self.install_progress_bar.stop()
            self.install_progress_bar.pack_forget()
            self.progress_label.pack_forget()
            self.update_install_step("Installation process completed")
            # Refresh the action button based on new status.
            self.install_or_start()

    def start_ollama(self):
        self.update_install_step("Starting Ollama service")
        self.progress_label = ttk.Label(self.install_frame, text="Starting Ollama service...", font=("Segoe UI", 10))
        self.progress_label.pack(pady=5)
        self.install_progress_bar.pack(fill=tk.X, pady=5)
        self.install_progress_bar.start()
        threading.Thread(target=self._start_ollama, daemon=True).start()

    def _start_ollama(self):
        try:
            if self.system == "Windows":
                ollama_path = os.path.expanduser("~\\AppData\\Local\\Programs\\Ollama\\ollama.exe")
                if os.path.exists(ollama_path):
                    self.log_install(f"Starting Ollama from: {ollama_path}")
                    subprocess.Popen([ollama_path, "serve"], creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    self.log_install("❌ Ollama executable not found")
            elif self.system == "Darwin":
                self.log_install("Starting Ollama on macOS...")
                subprocess.Popen(["open", "-a", "Ollama"])
            elif self.system == "Linux":
                self.log_install("Starting Ollama service on Linux...")
                subprocess.Popen(["ollama", "serve"])
            self.update_install_step("Waiting for service to start")
            time.sleep(5)
            self.check_ollama_running()
            if self.ollama_running:
                self.log_install("✅ Ollama service is now running!")
            else:
                self.log_install("⚠️ Ollama service failed to start. You may need to start it manually.")
        except Exception as e:
            self.log_install(f"❌ Error starting Ollama: {str(e)}")
        finally:
            self.install_progress_bar.stop()
            self.install_progress_bar.pack_forget()
            self.progress_label.pack_forget()
            self.update_install_step("Ollama service start process completed")
            self.install_or_start()

    # ----- Model Download Methods -----
    def download_models(self):
        selected_models = [model for model, var in self.model_vars.items() if var.get()]
        custom_model = self.custom_model_entry.get().strip()
        if custom_model:
            selected_models.append(custom_model)
        if not selected_models:
            messagebox.showinfo("No Models Selected", "Please select at least one model to download.")
            return
        self.download_button.config(state=tk.DISABLED)
        threading.Thread(target=lambda: self._download_models(selected_models), daemon=True).start()

    def _download_models(self, models):
        for model in models:
            try:
                self.model_step_label.config(text=f"Downloading {model}...")
                self.append_model_log(f"Downloading {model}...\n")
                response = requests.post(
                    "http://localhost:11434/api/pull",
                    json={"name": model},
                    stream=True
                )
                if response.status_code != 200:
                    self.append_model_log(f"❌ Failed to download {model}: HTTP {response.status_code}\n")
                    continue
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        if 'status' in data:
                            self.append_model_log(f"{data['status']}\n")
                        if data.get('completed', False):
                            self.append_model_log(f"✅ Successfully downloaded {model}\n\n")
                            self.root.after(0, lambda m=model: self.update_model_status(m))
                self.model_step_label.config(text=f"Finished downloading {model}")
            except Exception as e:
                self.append_model_log(f"❌ Error downloading {model}: {str(e)}\n")
        self.download_button.config(state=tk.NORMAL)

    def update_model_status(self, model):
        if hasattr(self, 'model_checkbuttons') and model in self.model_checkbuttons:
            self.model_checkbuttons[model].config(state=tk.DISABLED)
            new_text = f"{model} (Downloaded)"
            self.model_checkbuttons[model].config(text=new_text)


if __name__ == "__main__":
    root = tk.Tk()
    app = OllamaSetupWizard(root)
    root.mainloop()
