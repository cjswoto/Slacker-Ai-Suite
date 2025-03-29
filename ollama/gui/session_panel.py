import tkinter as tk
from tkinter import ttk, filedialog, messagebox


class SessionPanel:
    def __init__(self, parent, core_manager, on_session_change):
        self.parent = parent
        self.core_manager = core_manager
        self.on_session_change = on_session_change

        self.frame = ttk.LabelFrame(self.parent, text="Chat Sessions")
        self.frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.listbox = tk.Listbox(self.frame, bg="#363636", fg="#ffffff", selectbackground="#4a6da7")
        self.listbox.pack(fill=tk.BOTH, expand=True)
        self.listbox.bind("<Double-1>", self.open_selected_session)

        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        self.open_btn = ttk.Button(btn_frame, text="Open", command=self.open_selected_session)
        self.open_btn.pack(side=tk.LEFT)
        self.delete_btn = ttk.Button(btn_frame, text="Delete", command=self.delete_selected_session)
        self.delete_btn.pack(side=tk.LEFT, padx=5)
        self.export_btn = ttk.Button(btn_frame, text="Export", command=self.export_selected_session)
        self.export_btn.pack(side=tk.RIGHT)

    def refresh_sessions(self):
        self.listbox.delete(0, tk.END)
        session_names = []
        for session_id, session in self.core_manager.sessions.items():
            name = session.get("title", f"Session {session_id}")
            session_names.append(name)
        for name in session_names:
            self.listbox.insert(tk.END, name)

    def open_selected_session(self, event=None):
        if not self.listbox.curselection():
            return
        index = self.listbox.curselection()[0]
        session_name = self.listbox.get(index)
        for session_id, session in self.core_manager.sessions.items():
            if session.get("title") == session_name:
                if self.core_manager.load_session(session_id):
                    self.on_session_change(session)
                break

    def delete_selected_session(self):
        if not self.listbox.curselection():
            return
        index = self.listbox.curselection()[0]
        session_name = self.listbox.get(index)
        confirm = messagebox.askyesno("Confirm Deletion", f"Delete session '{session_name}'?")
        if confirm:
            for session_id, session in list(self.core_manager.sessions.items()):
                if session.get("title") == session_name:
                    self.core_manager.delete_session(session_id)
                    self.refresh_sessions()
                    break

    def export_selected_session(self):
        if not self.listbox.curselection():
            return
        index = self.listbox.curselection()[0]
        session_name = self.listbox.get(index)
        file_path = filedialog.asksaveasfilename(defaultextension=".json",
                                                 filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                                                 initialfile=f"OllamaChat_{session_name.replace(' ', '_')}.json")
        if file_path:
            for session_id, session in self.core_manager.sessions.items():
                if session.get("title") == session_name:
                    success = self.core_manager.export_session(session_id, file_path)
                    if success:
                        messagebox.showinfo("Export Successful", f"Session exported to {file_path}")
                    break
# This file was created by the setup script
