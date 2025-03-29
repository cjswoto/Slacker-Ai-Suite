import tkinter as tk
from tkinter import ttk


class SettingsPanel:
    def __init__(self, parent, core_manager, on_refresh_models):
        self.parent = parent
        self.core_manager = core_manager
        self.on_refresh_models = on_refresh_models

        self.frame = ttk.LabelFrame(self.parent, text="Model & Search Settings")
        self.frame.pack(fill=tk.X, padx=5, pady=5)

        # Model selection
        model_frame = ttk.Frame(self.frame)
        model_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(model_frame, text="Select Model:").pack(anchor=tk.W)
        self.model_combo = ttk.Combobox(model_frame)
        self.model_combo.pack(fill=tk.X)
        self.model_combo.bind("<<ComboboxSelected>>", self.model_selected)

        self.refresh_models_btn = ttk.Button(model_frame, text="Refresh Models", command=self.on_refresh_models)
        self.refresh_models_btn.pack(pady=5)

        # Search settings
        search_frame = ttk.LabelFrame(self.frame, text="Web Search Settings")
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(search_frame, text="Search Engine:").pack(anchor=tk.W)
        self.search_engine_combo = ttk.Combobox(search_frame, values=["DuckDuckGo", "DuckDuckGo API", "Google"])
        self.search_engine_combo.current(0)
        self.search_engine_combo.pack(fill=tk.X)

        ttk.Label(search_frame, text="Max Search Results:").pack(anchor=tk.W)
        self.max_results_spinbox = ttk.Spinbox(search_frame, from_=1, to=10, width=5)
        self.max_results_spinbox.set(3)
        self.max_results_spinbox.pack(anchor=tk.W)

        ttk.Label(search_frame, text="Search Timeout (seconds):").pack(anchor=tk.W)
        self.search_timeout_spinbox = ttk.Spinbox(search_frame, from_=5, to=30, width=5)
        self.search_timeout_spinbox.set(10)
        self.search_timeout_spinbox.pack(anchor=tk.W)

    def model_selected(self, event=None):
        selected = self.model_combo.get()
        self.core_manager.current_model = selected

    def update_settings(self):
        self.core_manager.search_engine = self.search_engine_combo.get()
        self.core_manager.max_search_results = int(self.max_results_spinbox.get())
        self.core_manager.search_timeout = int(self.search_timeout_spinbox.get())
# This file was created by the setup script
