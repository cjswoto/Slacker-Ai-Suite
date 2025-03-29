import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import subprocess
import threading
import os
import webbrowser

class CUDAWizard:
    def __init__(self, root):
        self.root = root
        self.root.title("CUDA Installation Wizard")
        self.root.geometry("650x450")
        self.style = tb.Style(theme="darkly")

        self.create_widgets()
        self.check_cuda()

    def create_widgets(self):
        self.status_label = tb.Label(self.root, text="Checking CUDA installation...", font=("Segoe UI", 14))
        self.status_label.pack(pady=15)

        self.log_box = tb.ScrolledText(self.root, state='disabled', height=14)
        self.log_box.pack(fill=BOTH, expand=True, padx=10, pady=10)

        self.action_button = tb.Button(self.root, text="Exit", command=self.root.quit, bootstyle="danger")
        self.action_button.pack(pady=5)

    def log(self, message):
        self.log_box.config(state='normal')
        self.log_box.insert(tk.END, f"{message}\n")
        self.log_box.see(tk.END)
        self.log_box.config(state='disabled')

    def check_cuda(self):
        def task():
            try:
                result = subprocess.run("nvcc --version", shell=True, capture_output=True, text=True)
                if "release" in result.stdout:
                    self.log(f"✅ CUDA detected:\n{result.stdout.strip()}")
                    self.status_label.config(text="✅ CUDA is already installed.")
                    self.action_button.config(text="Exit", bootstyle="success")
                else:
                    raise Exception("CUDA not detected.")
            except Exception as e:
                self.log(f"⚠️ CUDA not detected: {e}")
                self.status_label.config(text="⚠️ CUDA Toolkit not installed.")
                self.action_button.config(text="Download & Install CUDA Toolkit", command=self.download_cuda_page, bootstyle="warning")

        threading.Thread(target=task, daemon=True).start()

    def download_cuda_page(self):
        webbrowser.open("https://developer.nvidia.com/cuda-11-8-0-download-archive")
        messagebox.showinfo(
            "Download CUDA Toolkit",
            "1. Your browser will open NVIDIA's official CUDA Toolkit 11.8 download page.\n"
            "2. Download 'cuda_11.8.0_522.06_windows.exe' installer to your computer.\n"
            "3. After downloading, click OK and select the downloaded installer file to continue."
        )
        self.select_installer()

    def select_installer(self):
        installer_path = filedialog.askopenfilename(
            title="Select CUDA Installer",
            filetypes=[("Executable files", "*.exe")],
            initialdir=os.path.expanduser("~\\Downloads")
        )

        if installer_path and os.path.exists(installer_path):
            self.log(f"✅ Selected CUDA installer: {installer_path}")
            threading.Thread(target=self.launch_installer, args=(installer_path,), daemon=True).start()
        else:
            self.log("❌ No valid installer selected.")
            messagebox.showerror("Installation Error", "You must select a valid CUDA installer (.exe).")

    def launch_installer(self, installer_path):
        self.status_label.config(text="Launching CUDA Toolkit installer...")
        try:
            subprocess.run(installer_path, shell=True)
            self.log("✅ CUDA Installer launched successfully.")
            messagebox.showinfo(
                "Installation Started",
                "Follow the CUDA installer instructions. Once complete, you MUST restart your computer."
            )
            self.status_label.config(text="Installation started. Restart required afterward.")
            self.action_button.config(text="Exit", bootstyle="success")
        except Exception as e:
            self.log(f"❌ Error launching installer: {e}")
            messagebox.showerror("Installation Error", f"Could not launch CUDA installer:\n{e}")
            self.status_label.config(text="Installation failed. Please try again.")
            self.action_button.config(text="Exit", bootstyle="danger")

if __name__ == "__main__":
    root = tb.Window(themename="darkly")
    app = CUDAWizard(root)
    root.mainloop()
