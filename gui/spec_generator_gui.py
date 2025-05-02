# gui/spec_generator_gui.py
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import threading
import os
import sys
import subprocess
import json

from codegen.spec_generator import send_prompt_for_spec, list_available_models

class SpecGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AISuite Spec Generator")
        self.root.geometry("1000x800")
        self.root.configure(bg="#1E1E2F")

        # Header
        tk.Label(root, text="AISuite Spec Generator",
                 font=("Helvetica", 24, "bold"),
                 bg="#1E1E2F", fg="white").pack(pady=20)

        # Model selection
        frm = tk.Frame(root, bg="#1E1E2F")
        frm.pack(pady=5)
        tk.Label(frm, text="Select Model:", font=("Helvetica", 12),
                 bg="#1E1E2F", fg="white").pack(side=tk.LEFT, padx=5)
        self.model_var = tk.StringVar()
        self.model_dropdown = ttk.Combobox(frm, textvariable=self.model_var, width=40)
        self.model_dropdown.pack(side=tk.LEFT)
        tk.Button(frm, text="🔄 Refresh Models",
                  command=self.refresh_models,
                  bg="#3A3A5D", fg="white").pack(side=tk.LEFT, padx=5)

        # Prompt box
        self.prompt_entry = scrolledtext.ScrolledText(
            root, width=120, height=6,
            bg="#2D2D40", fg="white", font=("Courier", 11)
        )
        self.prompt_entry.pack(pady=10)

        # Generate button
        tk.Button(root, text="🚀 Generate and Build",
                  command=self.generate_and_stream,
                  bg="green", fg="white", font=("Helvetica", 14)
                 ).pack(pady=10)

        # Output log
        self.output = scrolledtext.ScrolledText(
            root, width=120, height=20,
            bg="#2D2D40", fg="white", font=("Courier", 11)
        )
        self.output.pack(pady=10)

        # Status bar & generated apps
        bottom = tk.Frame(root, bg="#1E1E2F")
        bottom.pack(fill=tk.X, pady=5)
        self.status = tk.Label(bottom, text="", font=("Helvetica", 12),
                               bg="#1E1E2F", fg="lightgray")
        self.status.pack(side=tk.LEFT, padx=10)

        apps_frame = tk.Frame(root, bg="#1E1E2F")
        apps_frame.pack(pady=10)
        tk.Label(apps_frame, text="🎁 Generated Apps:",
                 font=("Helvetica", 14, "bold"),
                 bg="#1E1E2F", fg="white").pack()
        self.apps_listbox = tk.Listbox(
            apps_frame, width=50, height=4,
            bg="white", fg="black", font=("Helvetica", 12)
        )
        self.apps_listbox.pack(pady=5)
        tk.Button(apps_frame, text="🚀 Launch",
                  command=self.launch_app,
                  bg="#3A3A5D", fg="white",
                  font=("Helvetica", 12)
                 ).pack()

        # initialize
        self.refresh_models()
        self.load_generated_apps()

    def refresh_models(self):
        models = list_available_models() or ["No Models Found"]
        self.model_dropdown['values'] = models
        self.model_var.set(models[0])

    def load_generated_apps(self):
        apps = []
        path = 'samples/accepted_apps.json'
        if os.path.exists(path):
            try:
                for app in json.load(open(path, encoding='utf-8')):
                    apps.append(app['name'])
            except:
                apps = []
        if not apps and os.path.isdir('generated_apps'):
            apps = sorted(d for d in os.listdir('generated_apps')
                          if os.path.isdir(os.path.join('generated_apps', d)))
        self.apps_listbox.delete(0, tk.END)
        for a in apps:
            self.apps_listbox.insert(tk.END, a)

    def launch_app(self):
        sel = self.apps_listbox.curselection()
        if not sel:
            return
        name = self.apps_listbox.get(sel[0])
        path = None
        accepted = 'samples/accepted_apps.json'
        if os.path.exists(accepted):
            for app in json.load(open(accepted, encoding='utf-8')):
                if app['name'] == name:
                    path = app['path']
        if not path:
            path = os.path.join('generated_apps', name)
        subprocess.Popen([sys.executable, 'main.py'], cwd=path)

    def generate_and_stream(self):
        prompt = self.prompt_entry.get('1.0', tk.END).strip()
        model  = self.model_var.get()
        if not prompt or model == 'No Models Found':
            messagebox.showerror('Error', 'Please enter a prompt and select a model.')
            return

        os.makedirs('samples', exist_ok=True)
        with open('samples/user_description.txt', 'w', encoding='utf-8') as f:
            f.write(prompt)

        self.output.delete('1.0', tk.END)
        self.status.config(text='🤔 Generating spec…')
        threading.Thread(target=self._pipeline, args=(model,), daemon=True).start()

    def _pipeline(self, model):
        steps = ['run_codegen_phase2.py', 'run_codegen_phase3.py']
        for step in steps:
            self.status.config(text=f'🔄 {step}…')
            proc = subprocess.Popen(
                [sys.executable, step],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace'
            )
            for line in proc.stdout:
                self.output.insert(tk.END, line)
                self.output.see(tk.END)
            proc.wait()
            if proc.returncode != 0:
                self.status.config(text=f'❌ {step} failed')
                return

        self.status.config(text='🎯 Done!')
        self.load_generated_apps()

def main():
    root = tk.Tk()
    SpecGeneratorApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
