# kb_gui.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from kb_manager import load_document_metadata, add_file, remove_file, rebuild_index


class KBGUI:
    def __init__(self, parent, on_index_updated_callback=None):
        """
        KB GUI allows the user to add files to the local KB, view the document list,
        and remove files. When files are added or removed, on_index_updated_callback
        is called to inform the main app to reload the index.
        """
        self.parent = parent
        self.on_index_updated_callback = on_index_updated_callback

        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.title_label = ttk.Label(self.frame, text="Local Knowledge Base Manager", font=("Segoe UI", 12, "bold"))
        self.title_label.pack(anchor=tk.W, pady=(0, 5))

        # Listbox for document list.
        list_frame = ttk.Frame(self.frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        self.listbox = tk.Listbox(list_frame, height=10)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        # Buttons
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill=tk.X, pady=5)
        self.add_button = ttk.Button(btn_frame, text="Add Files", command=self.add_files)
        self.add_button.pack(side=tk.LEFT, padx=(0, 5))
        self.remove_button = ttk.Button(btn_frame, text="Remove Selected", command=self.remove_selected)
        self.remove_button.pack(side=tk.LEFT, padx=(0, 5))
        self.refresh_button = ttk.Button(btn_frame, text="Refresh List", command=self.refresh_list)
        self.refresh_button.pack(side=tk.LEFT, padx=(0, 5))

        self.refresh_list()

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        metadata = load_document_metadata()
        for file_path, info in metadata.items():
            display_text = f"{info['filename']} - Last loaded: {info['last_loaded']}"
            self.listbox.insert(tk.END, display_text)

    def add_files(self):
        file_paths = filedialog.askopenfilenames(title="Select KB Files", filetypes=[("Text Files", "*.txt")])
        if not file_paths:
            return
        for file_path in file_paths:
            add_file(file_path)
        # Rebuild the index after adding files.
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
        metadata = load_document_metadata()
        file_paths = list(metadata.keys())
        file_path = file_paths[index]
        if remove_file(file_path):
            rebuild_index()
            self.refresh_list()
            messagebox.showinfo("KB Update", f"Removed file: {os.path.basename(file_path)}")
            if self.on_index_updated_callback:
                self.on_index_updated_callback()
        else:
            messagebox.showerror("KB Update", "Error removing file.")


if __name__ == "__main__":
    # For standalone testing of the KB GUI.
    root = tk.Tk()
    root.title("Local KB Manager")
    kb_gui = KBGUI(root)
    root.mainloop()
