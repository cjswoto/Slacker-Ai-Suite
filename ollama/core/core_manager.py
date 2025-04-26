# ollama/core/core_manager.py

import sys
import os
import time
import json

# Ensure project root is on sys.path
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
)

from . import api
from . import search
from . import session as session_manager
from transformers import pipeline
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract

from ollama.core.kb_helper import KnowledgeBaseHelper

CONFIG_PATH = os.path.join(os.getcwd(), "config.json")
LOG_FILE_PATH = os.path.join(os.getcwd(), "log.txt")


class CoreManager:
    def __init__(self):
        self.logging_enabled = True
        self.logging_level = 1
        self._log("Initializing CoreManager", 1)

        self.ollama_url = "http://localhost:11434"
        self.current_model = None

        self.web_search_enabled = True
        self.search_engine = "DuckDuckGo"
        self.max_search_results = 3
        self.search_timeout = 10
        self.search_debug_info = ""

        self.kb_debug_info = ""
        self.show_web_debug = False
        self.show_kb_debug = False

        self.current_session = None
        self.sessions = session_manager.load_sessions()
        self._log(f"Loaded sessions: {list(self.sessions.keys())}", 2)

        self.kb_helper = KnowledgeBaseHelper()
        self.kb_top_k = 3  # Default number of KB chunks to retrieve
        self.allowed_kb_files = None  # If set, restricts KB search to these files

        self._log("Initialized KnowledgeBaseHelper", 1)

        self._log("Initializing image captioning pipeline", 1)
        self.image_captioner = pipeline(
            "image-to-text",
            model="nlpconnect/vit-gpt2-image-captioning",
            use_fast=True
        )
        self.image_captioner.tokenizer.pad_token = self.image_captioner.tokenizer.eos_token
        self._log("CoreManager initialization complete", 1)

    def _log(self, message, level):
        if self.logging_enabled and level <= self.logging_level:
            ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            entry = f"[{ts}] [Level {level}] {message}\n"
            try:
                with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
                    f.write(entry)
            except Exception as e:
                print("Logging failed:", e)

    def set_logging_settings(self, enabled, level):
        self.logging_enabled = enabled
        self.logging_level = level
        self._log(f"Logging settings changed: enabled={enabled}, level={level}", 1)

    def set_kb_top_k(self, k):
        """
        Set how many KB chunks to retrieve per query.
        """
        self.kb_top_k = max(1, k)

    def set_allowed_kb_files(self, filenames):
        """
        Restrict KB search to only these files (filenames as list).
        """
        self.allowed_kb_files = filenames
        self.kb_helper.set_file_filter(filenames)

    def get_models(self):
        self._log("Fetching available models", 1)
        models = api.get_models(self.ollama_url)
        self._log(f"Models received: {models}", 2)
        return models

    def check_server_connection(self):
        self._log("Checking Ollama server connection", 1)
        ok = api.check_server_connection(self.ollama_url)
        self._log(f"Server connection status: {ok}", 2)
        return ok

    def generate_response(self, message, with_search=False, with_local_kb=True):
        self._log(f"Generating response for message: {message}", 1)
        start = time.time()

        search_results = None
        local_results = None
        self.kb_debug_info = ""

        if with_search and self.web_search_enabled:
            try:
                self._log("Performing web search", 1)
                data = search.perform_web_search(
                    message,
                    self.search_engine,
                    self.max_search_results,
                    self.search_timeout
                )
                search_results = data.get("results")
                self.search_debug_info = data.get("debug")
                self._log("Web search complete", 2)
            except Exception as e:
                self._log(f"Web search error: {e}", 1)

        if with_local_kb:
            try:
                selected_chunks, kb_debug_info = self.kb_helper.search_kb(message, top_k=self.kb_top_k)
                local_results = "\n".join(selected_chunks)
                self.kb_debug_info = kb_debug_info
                self._log(self.kb_debug_info, 2)
            except Exception as e:
                self._log(f"KB retrieval error: {e}", 1)

        prompt = message
        if search_results or local_results:
            prompt = (
                f"Question: {message}\n\n"
                f"Local Knowledge Context:\n{local_results or 'No local KB results.'}\n\n"
                f"Web Search Results:\n{search_results or 'No web search results.'}\n\n"
                "Please answer based on the context, or use your general knowledge."
            )
            self._log("Built prompt with context", 3)
            self._log(f"Prompt to AI (truncated):\n{prompt[:2000]}", 3)

        resp = api.generate_response(self.ollama_url, self.current_model, prompt)
        elapsed = time.time() - start
        self._log(f"Response generated in {elapsed:.2f}s", 2)

        return {
            **resp,
            "search_results": search_results,
            "kb_debug_info": self.kb_debug_info
        }

    def new_session(self):
        self._log("Creating new session", 1)
        session_id, session_data = session_manager.new_session(self.current_model)
        self.current_session = session_data
        self.sessions[session_id] = session_data
        self._log(f"New session {session_id} created", 2)
        return session_id

    def load_session(self, session_id):
        self._log(f"Loading session {session_id}", 1)
        data = session_manager.load_session(session_id)
        if data:
            self.current_session = data
            self._log("Session loaded successfully", 2)
            return True
        self._log("Failed to load session", 2)
        return False

    def delete_session(self, session_id):
        self._log(f"Deleting session {session_id}", 1)
        if session_manager.delete_session(session_id):
            self.sessions.pop(session_id, None)
            if self.current_session and self.current_session.get("id") == session_id:
                self.new_session()
            self._log("Session deleted", 2)
            return True
        self._log("Session deletion failed", 2)
        return False

    def export_session(self, session_id, file_path):
        self._log(f"Exporting session {session_id} to {file_path}", 1)
        session = self.sessions.get(session_id)
        if session:
            result = session_manager.export_session(session, file_path)
            self._log(f"Export result: {result}", 2)
            return result
        self._log("No such session to export", 2)
        return False

    def store_message_in_session(self, role, message):
        if not self.current_session:
            return
        self._log(f"Storing message: role={role}", 3)
        session_manager.store_message_in_session(self.current_session, role, message)

    def generate_image_caption(self, image_path):
        self._log(f"Captioning image: {image_path}", 1)
        try:
            img = Image.open(image_path)
            if img.mode != "RGB":
                img = img.convert("RGB")
            out = self.image_captioner(img)
            caption = out[0]["generated_text"].strip()
            self._log(f"Caption: {caption}", 2)
            return caption
        except Exception as e:
            self._log(f"Image caption error: {e}", 1)
            return f"[Error generating caption: {e}]"

    def generate_image_text(self, image_path):
        self._log(f"OCR image: {image_path}", 1)
        try:
            if os.path.exists(CONFIG_PATH):
                cfg = json.load(open(CONFIG_PATH, "r", encoding="utf-8"))
                pytesseract.pytesseract.tesseract_cmd = cfg["tesseract_path"]
                os.environ["TESSDATA_PREFIX"] = cfg["tessdata_prefix"]
            else:
                return "[Error: config.json not found]"

            img = Image.open(image_path).convert("L")
            enhancer = ImageEnhance.Contrast(img)
            proc = enhancer.enhance(2).filter(ImageFilter.MedianFilter())
            text = pytesseract.image_to_string(proc).strip()
            self._log(f"OCR text: {text}", 2)
            return text or "[No text detected]"
        except Exception as e:
            self._log(f"OCR error: {e}", 1)
            return f"[Error during OCR: {e}]"
