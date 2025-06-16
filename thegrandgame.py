import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import threading
import sys, os
import time

# Ensure the parent directory is in the path for CoreManager import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ollama.core.core_manager import CoreManager

class EndlessAdventureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Endless Text Adventure")
        self.root.geometry("1200x700")

        # Initialize CoreManager to handle AI requests and session management.
        self.core_manager = CoreManager()
        self.core_manager.show_web_debug = False
        self.core_manager.show_kb_debug = False

        # Store our own session log to display to the user.
        self.session_log = []

        # Create a horizontal PanedWindow: left for adventure; right for controls.
        self.paned = tb.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left frame: Adventure log and command entry.
        self.adventure_frame = tb.Frame(self.paned)
        self.paned.add(self.adventure_frame, weight=3)

        # Scrollable text area for the adventure log.
        self.adventure_log = tk.Text(self.adventure_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.adventure_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.scrollbar = tb.Scrollbar(self.adventure_log, orient=tk.VERTICAL, command=self.adventure_log.yview)
        self.adventure_log.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Input frame: command entry and submit button.
        self.input_frame = tb.Frame(self.adventure_frame)
        self.input_frame.pack(fill=tk.X, pady=(10, 0))

        self.command_entry = tb.Entry(self.input_frame)
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.command_entry.bind("<Return>", lambda event: self.process_command())

        self.submit_button = tb.Button(self.input_frame, text="Submit Command", command=self.process_command)
        self.submit_button.pack(side=tk.LEFT)

        # Progress indicator label.
        self.progress_label = tb.Label(self.adventure_frame, text="", font=("Helvetica", 10, "italic"))
        self.progress_label.pack(pady=(5, 0))

        # Right frame: Control panel for model selection and session controls.
        self.controls_frame = tb.Frame(self.paned)
        self.paned.add(self.controls_frame, weight=1)

        # LLM Model selection controls.
        tb.Label(self.controls_frame, text="Select LLM Model:").pack(pady=(10, 5))
        self.model_var = tk.StringVar()
        self.model_dropdown = tb.Combobox(self.controls_frame, textvariable=self.model_var, state="readonly")
        self.model_dropdown.pack(fill=tk.X, padx=10)
        self.model_dropdown.bind("<<ComboboxSelected>>", self.change_model)

        # Button to refresh available models.
        self.refresh_models_button = tb.Button(self.controls_frame, text="Refresh Models", command=self.refresh_models)
        self.refresh_models_button.pack(fill=tk.X, padx=10, pady=(5,10))

        # Session controls.
        self.new_session_button = tb.Button(self.controls_frame, text="New Session", command=self.new_session)
        self.new_session_button.pack(fill=tk.X, padx=10, pady=(5,10))

        self.show_log_button = tb.Button(self.controls_frame, text="Show Session Log", command=self.show_session_log)
        self.show_log_button.pack(fill=tk.X, padx=10, pady=(5,10))

        # Start background tasks and a new session.
        self.root.after(100, self.start_background_tasks)
        self.new_session()

    def start_background_tasks(self):
        threading.Thread(target=self.refresh_models, daemon=True).start()
        threading.Thread(target=self.check_server_connection, daemon=True).start()

    def refresh_models(self):
        models = self.core_manager.get_models()
        if models:
            # Update the dropdown list.
            self.model_dropdown['values'] = models
            if not self.core_manager.current_model:
                self.core_manager.current_model = models[0]
                self.model_var.set(models[0])
            # If the current model is not in the refreshed list, update it.
            elif self.core_manager.current_model not in models:
                self.core_manager.current_model = models[0]
                self.model_var.set(models[0])

    def change_model(self, event):
        selected_model = self.model_var.get()
        self.core_manager.current_model = selected_model
        self.append_log("🔄 LLM model changed to: " + selected_model)

    def check_server_connection(self):
        # You can add visual cues based on connection status if needed.
        is_connected = self.core_manager.check_server_connection()

    def new_session(self):
        session_id = self.core_manager.new_session()
        self.session_log = []  # Clear our stored log.
        self.append_log("🌟 A new adventure begins! (Session ID: {})".format(session_id))

    def process_command(self):
        user_input = self.command_entry.get().strip()
        if not user_input:
            return
        # Append the player's command to the adventure log.
        self.append_log("🧙 You: " + user_input)
        self.command_entry.delete(0, tk.END)
        # Show the progress indicator.
        self.progress_label.config(text="🤖 AI is thinking...")
        # Start a thread to get the AI response.
        threading.Thread(target=self.generate_response, args=(user_input,), daemon=True).start()

    def generate_response(self, user_input):
        # Prepend adventure instructions to the prompt so the AI acts as a text adventure game engine.
        prompt = (
            "You are a text adventure game engine. Your role is to act as the narrator "
            "of an endless interactive text adventure. Respond in a creative, descriptive, and "
            "consistent style, detailing the environment, events, and challenges. The player's command is: "
            "'" + user_input + "'."
        )
        with_search = True  # Enable web search if required by CoreManager.
        response_data = self.core_manager.generate_response(
            prompt,
            with_search=with_search,
            with_local_kb=self.core_manager.local_kb_enabled
        )
        if response_data.get("success"):
            response = response_data.get("ai_response", "")
            self.root.after(0, lambda: self.append_log("📜 " + response))
            self.core_manager.store_message_in_session("assistant", response)
        else:
            error = response_data.get("error", "Unknown error")
            self.root.after(0, lambda: self.append_log("⚠️ Error: " + error))
        # Hide the progress indicator.
        self.root.after(0, lambda: self.progress_label.config(text=""))

    def append_log(self, message):
        self.session_log.append(message)
        self.adventure_log.configure(state=tk.NORMAL)
        self.adventure_log.insert(tk.END, message + "\n\n")
        self.adventure_log.configure(state=tk.DISABLED)
        self.adventure_log.see(tk.END)

    def show_session_log(self):
        # Create a new window to display the session log.
        log_window = tk.Toplevel(self.root)
        log_window.title("Session Log")
        log_window.geometry("600x400")
        text_area = tk.Text(log_window, wrap=tk.WORD, state=tk.NORMAL)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        # Insert the stored session log.
        for line in self.session_log:
            text_area.insert(tk.END, line + "\n\n")
        text_area.configure(state=tk.DISABLED)

if __name__ == "__main__":
    root = tb.Window(themename="darkly")
    app = EndlessAdventureApp(root)
    root.mainloop()
