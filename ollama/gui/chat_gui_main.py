import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import threading
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ollama.core.core_manager import CoreManager
from ollama.gui.chat_interface import ChatInterface
from ollama.gui.settings_panel import SettingsPanel
from ollama.gui.session_panel import SessionPanel

class OllamaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OllamaChat - Local LLM Interface")
        self.root.geometry("1200x800")

        # Create CoreManager instance.
        self.core_manager = CoreManager()
        # Set default debug flags (initially both off).
        self.core_manager.show_web_debug = False
        self.core_manager.show_kb_debug = False

        # Create a PanedWindow to split chat and settings.
        self.paned = tb.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Chat area frame.
        self.chat_frame = tb.Frame(self.paned)
        self.paned.add(self.chat_frame, weight=3)
        # Settings area frame.
        self.settings_frame = tb.Frame(self.paned)
        self.paned.add(self.settings_frame, weight=1)

        # Create ChatInterface with required callbacks.
        self.chat_interface = ChatInterface(
            self.chat_frame,
            self.process_message,
            self.new_session,
            self.update_search_settings  # This callback receives three booleans.
        )

        # Create SettingsPanel.
        self.settings_panel = SettingsPanel(self.settings_frame, self.core_manager, self.refresh_models)

        # Create SessionPanel.
        self.session_panel = SessionPanel(self.settings_frame, self.core_manager, self.on_session_change)
        self.session_panel.refresh_sessions()

        # Start background tasks.
        self.root.after(100, self.start_background_tasks)
        # New session at startup.
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
        is_connected = self.core_manager.check_server_connection()
        # Optionally update a status indicator here.

    def process_message(self, user_input):
        def task():
            with_search = True
            response_data = self.core_manager.generate_response(user_input, with_search=with_search)
            if response_data.get("success"):
                response = response_data.get("ai_response", "")
                self.chat_interface.display_message("🤖 AI", response, tag="ai")
                self.core_manager.store_message_in_session("assistant", response)
            else:
                error = response_data.get("error", "Unknown error")
                self.chat_interface.display_error(error)
            # Display web debug info if enabled.
            if self.core_manager.search_debug_info and self.core_manager.show_web_debug:
                self.chat_interface.display_search_info(self.core_manager.search_debug_info)
            # Display KB debug info if available and enabled.
            if response_data.get("kb_debug_info") and self.core_manager.show_kb_debug:
                self.chat_interface.display_search_info(response_data.get("kb_debug_info"))
        threading.Thread(target=task, daemon=True).start()

    def new_session(self):
        session_id = self.core_manager.new_session()
        self.session_panel.refresh_sessions()

    def on_session_change(self, session):
        # Update the chat interface with session messages if desired.
        pass

    def update_search_settings(self, web_search_enabled, show_web_debug, show_kb_debug):
        self.core_manager.web_search_enabled = web_search_enabled
        self.core_manager.show_web_debug = show_web_debug
        self.core_manager.show_kb_debug = show_kb_debug

if __name__ == "__main__":
    root = tb.Window(themename="darkly")
    app = OllamaApp(root)
    root.mainloop()
