# kb_gui.py
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from kb_manager import load_document_metadata, add_file, remove_file, rebuild_index, scan_and_update_kb

class KBGUI:
    def __init__(self, parent, on_index_updated_callback=None):
        self.parent = parent
        self.on_index_updated_callback = on_index_updated_callback

        self.frame = ttk.Labelframe(self.parent, text="📚 Local Knowledge Base", padding=10)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.title_label = ttk.Label(self.frame, text="Manage your local KB documents", font=("Segoe UI", 11, "bold"))
        self.title_label.pack(anchor=tk.W, pady=(0, 5))

        list_frame = ttk.Frame(self.frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        self.listbox = tk.Listbox(list_frame, height=12, bg="#2b2b2b", fg="#ffffff", selectbackground="#007acc")
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill=tk.X, pady=5)
        self.add_button = ttk.Button(btn_frame, text="➕ Add Files", command=self.add_files)
        self.add_button.pack(side=tk.LEFT, padx=(0, 5))
        self.remove_button = ttk.Button(btn_frame, text="🗑️ Remove Selected", command=self.remove_selected)
        self.remove_button.pack(side=tk.LEFT, padx=(0, 5))
        self.refresh_button = ttk.Button(btn_frame, text="🔄 Refresh", command=self.refresh_list)
        self.refresh_button.pack(side=tk.LEFT, padx=(0, 5))
        self.rescan_button = ttk.Button(btn_frame, text="🔍 Scan for New Files", command=self.scan_for_new_files)
        self.rescan_button.pack(side=tk.LEFT, padx=(0, 5))

        self.display_to_path = {}
        self.refresh_list()

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        self.display_to_path = {}
        metadata = load_document_metadata()
        for file_path, info in metadata.items():
            display_text = f"{info['filename']} (Last loaded: {info['last_loaded']})"
            self.listbox.insert(tk.END, display_text)
            self.display_to_path[display_text] = file_path

    def add_files(self):
        file_paths = filedialog.askopenfilenames(title="Select KB Files", filetypes=[("Text Files", "*.txt")])
        if not file_paths:
            return
        for file_path in file_paths:
            add_file(file_path)
        rebuild_index()
        self.refresh_list()
        messagebox.showinfo("KB Update", "Selected files have been added and indexed.")
        if self.on_index_updated_callback:
            self.on_index_updated_callback()

    def remove_selected(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Remove File", "No file selected.")
            return
        index = selection[0]
        display_text = self.listbox.get(index)
        file_path = self.display_to_path.get(display_text)
        if not file_path:
            messagebox.showerror("KB Update", "File mapping not found.")
            return

        if remove_file(file_path):
            rebuild_index()
            self.refresh_list()
            messagebox.showinfo("KB Update", f"Removed file: {os.path.basename(file_path)}")
            if self.on_index_updated_callback:
                self.on_index_updated_callback()
        else:
            messagebox.showerror("KB Update", "Error removing file.")

    def scan_for_new_files(self):
        updated = scan_and_update_kb()
        if updated:
            rebuild_index()
            self.refresh_list()
            messagebox.showinfo("KB Scan", "New files found and indexed.")
            if self.on_index_updated_callback:
                self.on_index_updated_callback()
        else:
            self.refresh_list()
            messagebox.showinfo("KB Scan", "No new files found.")

if __name__ == "__main__":
    import ttkbootstrap as tb
    root = tb.Window(themename="darkly")
    root.title("Local KB Manager")
    kb_gui = KBGUI(root)
    root.mainloop()
