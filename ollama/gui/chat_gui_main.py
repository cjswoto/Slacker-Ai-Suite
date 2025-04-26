# chat_gui_main.py

import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import threading
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ollama.core.core_manager import CoreManager
from ollama.gui.chat_interface import ChatInterface
from ollama.gui.settings_panel import SettingsPanel
from ollama.gui.session_panel import SessionPanel
from tkinter import filedialog

class OllamaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OllamaChat - Local LLM Interface")
        self.root.geometry("1200x800")

        self.core_manager = CoreManager()
        self.core_manager.show_web_debug = False
        self.core_manager.show_kb_debug = False

        self.paned = tb.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.chat_frame = tb.Frame(self.paned)
        self.paned.add(self.chat_frame, weight=3)
        self.settings_frame = tb.Frame(self.paned)
        self.paned.add(self.settings_frame, weight=1)

        self.chat_interface = ChatInterface(
            self.chat_frame,
            self.process_message,
            self.new_session,
            self.update_search_settings,
            self.update_logging_settings,
            self.attach_image
        )

        self.settings_panel = SettingsPanel(self.settings_frame, self.core_manager, self.refresh_models)
        self.session_panel = SessionPanel(self.settings_frame, self.core_manager, self.on_session_change)
        self.session_panel.refresh_sessions()

        self.root.after(100, self.start_background_tasks)
        self.new_session()

    def start_background_tasks(self):
        threading.Thread(target=self.refresh_models, daemon=True).start()
        threading.Thread(target=self.check_server_connection, daemon=True).start()

    def refresh_models(self):
        models = self.core_manager.get_models()
        if models:
            self.settings_panel.model_combo['values'] = models
            if not self.core_manager.current_model:
                self.core_manager.current_model = models[0]
                self.settings_panel.model_combo.set(models[0])

    def check_server_connection(self):
        self.core_manager.check_server_connection()

    def process_message(self, user_input):
        self.chat_interface.start_progress_indicator("Generating response")
        def task():
            response_data = self.core_manager.generate_response(user_input, with_search=True)
            if response_data.get("success"):
                ai_resp = response_data.get("ai_response", "")
                self.root.after(0, lambda: self.chat_interface.display_message("🤖 AI", ai_resp, tag="ai"))
                self.core_manager.store_message_in_session("assistant", ai_resp)
            else:
                err = response_data.get("error", "Unknown error")
                self.root.after(0, lambda: self.chat_interface.display_error(err))

            if self.core_manager.show_web_debug and self.core_manager.search_debug_info:
                self.root.after(0, lambda: self.chat_interface.display_search_info(self.core_manager.search_debug_info))
            if self.core_manager.show_kb_debug and response_data.get("kb_debug_info"):
                self.root.after(0, lambda: self.chat_interface.display_search_info(response_data.get("kb_debug_info")))

            self.root.after(0, self.chat_interface.stop_progress_indicator)
        threading.Thread(target=task, daemon=True).start()

    def new_session(self):
        self.core_manager.new_session()
        self.session_panel.refresh_sessions()

    def on_session_change(self, session):
        """
        When a session is selected, clear the chat display and replay all stored messages.
        """
        # Clear existing chat display
        self.chat_interface.chat_display.config(state=tk.NORMAL)
        self.chat_interface.chat_display.delete("1.0", tk.END)

        # Replay stored messages
        for msg in session.get("messages", []):
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                self.chat_interface.display_message("🧑 You", content, tag="user")
            else:
                self.chat_interface.display_message("🤖 AI", content, tag="ai")

        # Lock display again
        self.chat_interface.chat_display.config(state=tk.DISABLED)

    def update_search_settings(self, web_search_enabled, show_web_debug, show_kb_debug):
        self.core_manager.web_search_enabled = web_search_enabled
        self.core_manager.show_web_debug = show_web_debug
        self.core_manager.show_kb_debug = show_kb_debug

    def update_logging_settings(self, logging_enabled, logging_level):
        self.core_manager.set_logging_settings(logging_enabled, logging_level)

    def attach_image(self, mode):
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        if file_path:
            if mode == "OCR":
                return self.core_manager.generate_image_text(file_path)
            else:
                return self.core_manager.generate_image_caption(file_path)
        return None

if __name__ == "__main__":
    root = tb.Window(themename="darkly")
    app = OllamaApp(root)
    root.mainloop()
