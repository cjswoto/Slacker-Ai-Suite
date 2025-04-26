# ollama/gui/settings_panel.py

import os
import tkinter as tk
from tkinter import ttk
from ollama.kb.kb_manager import (
    load_document_metadata,
    add_file,
    remove_file,
    rebuild_index,
    scan_and_update_kb
)

class SettingsPanel:
    def __init__(self, parent, core_manager, on_refresh_models):
        self.parent = parent
        self.core_manager = core_manager
        self.on_refresh_models = on_refresh_models

        self.frame = ttk.LabelFrame(self.parent, text="Model & Search Settings")
        self.frame.pack(fill=tk.X, padx=5, pady=5)

        model_frame = ttk.Frame(self.frame)
        model_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(model_frame, text="Select Model:").pack(anchor=tk.W)
        self.model_combo = ttk.Combobox(model_frame)
        self.model_combo.pack(fill=tk.X)
        self.model_combo.bind("<<ComboboxSelected>>", self.model_selected)

        self.refresh_models_btn = ttk.Button(model_frame, text="Refresh Models", command=self.on_refresh_models)
        self.refresh_models_btn.pack(pady=5)

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

        kb_frame = ttk.LabelFrame(self.frame, text="Knowledge Base Settings")
        kb_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(kb_frame, text="Number of KB Chunks to Use:").pack(anchor=tk.W)
        self.kb_top_k_spinbox = ttk.Spinbox(kb_frame, from_=1, to=10, width=5, command=self.update_kb_top_k)
        self.kb_top_k_spinbox.set(3)
        self.kb_top_k_spinbox.pack(anchor=tk.W)

        ttk.Label(kb_frame, text="Allowed KB Files:").pack(anchor=tk.W)
        self.kb_file_listbox = tk.Listbox(kb_frame, selectmode=tk.MULTIPLE, height=6, bg="#2b2b2b", fg="#ffffff")
        self.kb_file_listbox.pack(fill=tk.X, pady=5)

        apply_filter_btn = ttk.Button(kb_frame, text="Apply File Filter", command=self.apply_kb_file_filter)
        apply_filter_btn.pack(pady=5)

        self.refresh_kb_file_list()

    def model_selected(self, event=None):
        selected = self.model_combo.get()
        self.core_manager.current_model = selected

    def update_settings(self):
        self.core_manager.search_engine = self.search_engine_combo.get()
        self.core_manager.max_search_results = int(self.max_results_spinbox.get())
        self.core_manager.search_timeout = int(self.search_timeout_spinbox.get())

    def update_kb_top_k(self):
        try:
            top_k = int(self.kb_top_k_spinbox.get())
            self.core_manager.set_kb_top_k(top_k)
        except Exception as e:
            print("Failed to update KB top_k:", e)

    def refresh_kb_file_list(self):
        self.kb_file_listbox.delete(0, tk.END)
        files = set()

        try:
            if not hasattr(self.core_manager, "kb_helper") or not self.core_manager.kb_helper.kb_metadata:
                from ollama.core.kb_helper import KnowledgeBaseHelper
                self.core_manager.kb_helper = KnowledgeBaseHelper()

            for meta in self.core_manager.kb_helper.kb_metadata:
                source = meta.get("source", "")
                if source:
                    files.add(os.path.basename(source))

            if not files:
                metadata = load_document_metadata()
                for record in metadata.values():
                    if "filename" in record:
                        files.add(record["filename"])

        except Exception as e:
            print("KB file list error:", e)

        for file in sorted(files):
            self.kb_file_listbox.insert(tk.END, file)

    def apply_kb_file_filter(self):
        selected_indices = self.kb_file_listbox.curselection()
        selected_files = [self.kb_file_listbox.get(i) for i in selected_indices]
        if selected_files:
            self.core_manager.set_allowed_kb_files(selected_files)
        else:
            self.core_manager.set_allowed_kb_files(None)
