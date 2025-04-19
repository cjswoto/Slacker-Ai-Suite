import tkinter as tk
from tkinter import scrolledtext, ttk, filedialog

class ChatInterface:
    def __init__(
        self,
        parent,
        on_send_callback,
        on_new_session_callback,
        on_update_search_settings_callback,
        on_update_logging_settings_callback,
        on_attach_image_callback=None
    ):
        """
        :param parent: The parent widget/frame.
        :param on_send_callback: function(user_text) -> None.
        :param on_new_session_callback: function() -> None.
        :param on_update_search_settings_callback: function(bool, bool, bool) -> None.
        :param on_update_logging_settings_callback: function(bool, int) -> None.
        :param on_attach_image_callback: function(mode) -> image_text (string) or None.
        """
        self.parent = parent
        self.on_send_callback = on_send_callback
        self.on_new_session_callback = on_new_session_callback
        self.on_update_search_settings_callback = on_update_search_settings_callback
        self.on_update_logging_settings_callback = on_update_logging_settings_callback
        self.on_attach_image_callback = on_attach_image_callback

        self.attached_image_caption = None

        self.web_search_enabled = tk.BooleanVar(value=True)
        self.show_web_debug = tk.BooleanVar(value=False)
        self.show_kb_debug = tk.BooleanVar(value=False)

        # New variables for logging settings using numeric values.
        self.logging_enabled = tk.BooleanVar(value=True)
        self.logging_level = tk.IntVar(value=1)  # Options: 1, 2, or 3

        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.chat_label = ttk.Label(
            self.frame, text="🗨️ Conversation", font=("Segoe UI", 12, "bold")
        )
        self.chat_label.pack(anchor=tk.W, pady=(0, 5))

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

        self.progress_frame = ttk.Frame(self.frame)
        self.progress_frame.pack(fill=tk.X, pady=(0, 5))
        self.progress_label = ttk.Label(self.progress_frame, text="", font=("Segoe UI", 9), foreground="red")
        self.progress_label.pack(anchor=tk.W, side=tk.LEFT)

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

        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill=tk.X)

        # Attach Image button.
        self.attach_image_button = ttk.Button(
            button_frame,
            text="Attach Image 🖼️",
            command=self.attach_image
        )
        self.attach_image_button.pack(side=tk.LEFT, padx=5)

        # Mode selector for image processing.
        self.image_mode_combo = ttk.Combobox(button_frame, values=[1, 2], width=10)
        self.image_mode_combo.set(1)  # Default mode (1 for Captioning, 2 for OCR)
        self.image_mode_combo.pack(side=tk.LEFT, padx=5)

        self.web_search_checkbox = ttk.Checkbutton(
            button_frame,
            text="Enable Web Search",
            variable=self.web_search_enabled,
            style="success.TCheckbutton",
            command=self.update_search_settings
        )
        self.web_search_checkbox.pack(side=tk.LEFT)

        self.web_debug_checkbox = ttk.Checkbutton(
            button_frame,
            text="Show Web Debug Info",
            variable=self.show_web_debug,
            style="info.TCheckbutton",
            command=self.update_search_settings
        )
        self.web_debug_checkbox.pack(side=tk.LEFT, padx=10)

        self.kb_debug_checkbox = ttk.Checkbutton(
            button_frame,
            text="Show KB Debug Info",
            variable=self.show_kb_debug,
            style="info.TCheckbutton",
            command=self.update_search_settings
        )
        self.kb_debug_checkbox.pack(side=tk.LEFT, padx=10)

        # New controls for logging settings using numeric levels.
        self.logging_checkbox = ttk.Checkbutton(
            button_frame,
            text="Enable Logging",
            variable=self.logging_enabled,
            style="warning.TCheckbutton",
            command=self.update_logging_settings
        )
        self.logging_checkbox.pack(side=tk.LEFT, padx=10)

        self.logging_level_combo = ttk.Combobox(
            button_frame,
            values=[1, 2, 3],
            textvariable=self.logging_level,
            width=5
        )
        self.logging_level_combo.set(1)
        self.logging_level_combo.bind("<<ComboboxSelected>>", lambda e: self.update_logging_settings())
        self.logging_level_combo.pack(side=tk.LEFT, padx=5)

        self.send_button = ttk.Button(
            button_frame,
            text="Send 📤",
            style="success.TButton",
            command=self.send_message
        )
        self.send_button.pack(side=tk.RIGHT)

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
        if not user_input and not self.attached_image_caption:
            return
        if self.attached_image_caption:
            user_input = f"Image Context: {self.attached_image_caption}\n{user_input}"
            self.attached_image_caption = None
        self.message_input.delete("1.0", tk.END)
        self.display_message("🧑 You", user_input, tag="user")
        self.on_send_callback(user_input)

    def update_search_settings(self):
        self.on_update_search_settings_callback(
            self.web_search_enabled.get(),
            self.show_web_debug.get(),
            self.show_kb_debug.get()
        )

    def update_logging_settings(self):
        self.on_update_logging_settings_callback(
            self.logging_enabled.get(),
            self.logging_level.get()
        )

    def attach_image(self):
        """Callback for Attach Image: uses selected mode (1 for Captioning, 2 for OCR)."""
        mode = int(self.image_mode_combo.get())
        if self.on_attach_image_callback:
            caption = self.on_attach_image_callback("OCR" if mode == 2 else "Captioning")
            if caption:
                self.attached_image_caption = caption
                self.display_message("🖼️ Image", f"Attached image ({'OCR' if mode == 2 else 'Captioning'}): {caption}", tag="image")

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

    def start_progress_indicator(self, text="Working"):
        self._progress_running = True
        self._progress_text = text
        self._progress_idx = 0
        self._spinner_chars = ["|", "/", "-", "\\"]
        self._animate_progress()

    def _animate_progress(self):
        if not self._progress_running:
            return
        spinner = self._spinner_chars[self._progress_idx % len(self._spinner_chars)]
        self.set_progress_text(f"{self._progress_text}... {spinner}")
        self._progress_idx += 1
        self.parent.after(200, self._animate_progress)

    def stop_progress_indicator(self):
        self._progress_running = False
        self.set_progress_text("")
