import tkinter as tk
from tkinter import scrolledtext, ttk

class ChatInterface:
    def __init__(
        self,
        parent,
        on_send_callback,
        on_new_session_callback,
        on_update_search_settings_callback
    ):
        """
        :param parent: The parent widget/frame.
        :param on_send_callback: function(user_text) -> None.
        :param on_new_session_callback: function() -> None.
        :param on_update_search_settings_callback: function(bool, bool, bool) -> None.
            (Parameters: web_search_enabled, show_web_debug, show_kb_debug)
        """
        self.parent = parent
        self.on_send_callback = on_send_callback
        self.on_new_session_callback = on_new_session_callback
        self.on_update_search_settings_callback = on_update_search_settings_callback

        # Variables for checkboxes.
        self.web_search_enabled = tk.BooleanVar(value=True)
        self.show_web_debug = tk.BooleanVar(value=False)
        self.show_kb_debug = tk.BooleanVar(value=False)

        # Main frame.
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # Label: "Conversation".
        self.chat_label = ttk.Label(
            self.frame, text="🗨️ Conversation", font=("Segoe UI", 12, "bold")
        )
        self.chat_label.pack(anchor=tk.W, pady=(0, 5))

        # Chat display.
        self.chat_display = scrolledtext.ScrolledText(
            self.frame,
            wrap=tk.WORD,
            bg="#2b2b2b",
            fg="#ffffff",
            insertbackground="white",
            font=("Segoe UI", 10),
            height=20,
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.chat_display.config(state=tk.DISABLED)

        # Progress label.
        self.progress_frame = ttk.Frame(self.frame)
        self.progress_frame.pack(fill=tk.X, pady=(0, 5))
        self.progress_label = ttk.Label(self.progress_frame, text="", font=("Segoe UI", 9))
        self.progress_label.pack(anchor=tk.W, side=tk.LEFT)

        # Message input.
        self.message_input = scrolledtext.ScrolledText(
            self.frame,
            height=4,
            wrap=tk.WORD,
            bg="#363636",
            fg="#ffffff",
            insertbackground="white",
            font=("Segoe UI", 10),
        )
        self.message_input.pack(fill=tk.X, pady=(0, 5))
        self.message_input.bind("<Return>", self.handle_return_key)
        self.message_input.bind("<Shift-Return>", lambda e: None)

        # Bottom button/checkbox row.
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill=tk.X)

        # "Enable Web Search" checkbox.
        self.web_search_checkbox = ttk.Checkbutton(
            button_frame,
            text="Enable Web Search",
            variable=self.web_search_enabled,
            style="success.TCheckbutton",
            command=self.update_search_settings
        )
        self.web_search_checkbox.pack(side=tk.LEFT)

        # "Show Web Debug Info" checkbox.
        self.web_debug_checkbox = ttk.Checkbutton(
            button_frame,
            text="Show Web Debug Info",
            variable=self.show_web_debug,
            style="info.TCheckbutton",
            command=self.update_search_settings
        )
        self.web_debug_checkbox.pack(side=tk.LEFT, padx=10)

        # "Show KB Debug Info" checkbox.
        self.kb_debug_checkbox = ttk.Checkbutton(
            button_frame,
            text="Show KB Debug Info",
            variable=self.show_kb_debug,
            style="info.TCheckbutton",
            command=self.update_search_settings
        )
        self.kb_debug_checkbox.pack(side=tk.LEFT, padx=10)

        # "Send" button.
        self.send_button = ttk.Button(
            button_frame,
            text="Send 📤",
            style="success.TButton",
            command=self.send_message
        )
        self.send_button.pack(side=tk.RIGHT)

        # "New Session" button.
        self.new_session_button = ttk.Button(
            button_frame,
            text="New Session 🗒️",
            style="info.TButton",
            command=self.on_new_session_callback
        )
        self.new_session_button.pack(side=tk.RIGHT, padx=5)

    def handle_return_key(self, event):
        if not event.state & 0x1:
            self.send_message()
            return "break"
        return None

    def send_message(self):
        user_input = self.message_input.get("1.0", tk.END).strip()
        if not user_input:
            return
        self.message_input.delete("1.0", tk.END)
        self.display_message("🧑 You", user_input, tag="user")
        self.on_send_callback(user_input)

    def update_search_settings(self):
        # Pass the current checkbox states to the callback.
        self.on_update_search_settings_callback(
            self.web_search_enabled.get(),
            self.show_web_debug.get(),
            self.show_kb_debug.get()
        )

    def display_message(self, sender, message, tag=None):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"\n{sender}: {message}\n\n", tag)
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def display_search_info(self, info):
        self.display_message("🔍", info, tag="search_info")

    def display_error(self, error_message):
        self.display_message("❌ Error", error_message, tag="error")

    def set_progress_text(self, text):
        self.progress_label.config(text=text)
