import time
from . import api
from . import search
from . import session as session_manager
from transformers import pipeline
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import os
import json

# Define the configuration file path in the application's root directory.
CONFIG_PATH = os.path.join(os.getcwd(), "config.json")
LOG_FILE_PATH = os.path.join(os.getcwd(), "log.txt")

class CoreManager:
    def __init__(self):
        # Logging configuration: logging_enabled = True/False, logging_level: 1, 2, or 3
        self.logging_enabled = True
        self.logging_level = 1  # Default to level 1 (lowest)

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
        self._log(f"Loaded sessions: {self.sessions}", 2)

        self.kb_index = None
        self.kb_chunks = []
        self.kb_metadata = []

        # Initialize an image captioning pipeline with use_fast=True.
        self._log("Initializing image captioning pipeline", 1)
        self.image_captioner = pipeline(
            "image-to-text",
            model="nlpconnect/vit-gpt2-image-captioning",
            use_fast=True
        )
        # Fix the attention mask warning by setting pad_token to eos_token.
        self.image_captioner.tokenizer.pad_token = self.image_captioner.tokenizer.eos_token
        self._log("CoreManager initialization complete", 1)

    def _log(self, message, level):
        """
        Inline logging function.
        level: 1, 2, or 3.
        Only logs messages if logging is enabled and the message's level is less than or equal to current logging level.
        """
        if self.logging_enabled and level <= self.logging_level:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            log_message = f"[{timestamp}] [Level {level}] {message}\n"
            try:
                with open(LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
                    log_file.write(log_message)
            except Exception as e:
                # In case of file write error, print to console.
                print("Logging failed:", e)

    def set_logging_settings(self, enabled, level):
        """
        External method to update logging settings.
        :param enabled: Boolean indicating if logging is enabled.
        :param level: Integer (1, 2, or 3) for logging verbosity.
        """
        self.logging_enabled = enabled
        self.logging_level = level
        self._log(f"Logging settings updated: enabled={enabled}, level={level}", 1)

    def get_models(self):
        self._log("Calling get_models", 1)
        models = api.get_models(self.ollama_url)
        self._log(f"Models received: {models}", 2)
        return models

    def check_server_connection(self):
        self._log("Checking server connection", 1)
        result = api.check_server_connection(self.ollama_url)
        self._log(f"Server connection result: {result}", 2)
        return result

    def generate_response(self, message, with_search=False, with_local_kb=True):
        self._log(f"Generating response for message: {message}", 1)
        start_time = time.time()
        search_results = None
        local_results = None
        kb_debug_info = ""
        if with_search and self.web_search_enabled:
            self._log("Performing web search", 1)
            search_result_data = search.perform_web_search(
                message, self.search_engine, self.max_search_results, self.search_timeout
            )
            search_results = search_result_data.get("results")
            self.search_debug_info = search_result_data.get("debug")
            self._log(f"Web search results: {search_results}", 2)
            self._log(f"Web search debug info: {self.search_debug_info}", 3)
        else:
            self._log("Web search not enabled or skipped", 2)
        kb_debug_info = "Local KB retrieval disabled."
        prompt = message
        if search_results or local_results:
            prompt = f"""Question: {message}

Local Knowledge Context:
{local_results or "No local KB results."}

Web Search Results:
{search_results or "No web search results."}

Please answer the question based on the provided context. If the context isn’t relevant, use your general knowledge to provide the best answer possible."""
            self._log(f"Generated prompt for AI: {prompt}", 3)
        response = api.generate_response(self.ollama_url, self.current_model, prompt)
        elapsed = time.time() - start_time
        self._log(f"Response generated in {elapsed:.2f} seconds", 2)
        return {
            **response,
            "search_results": search_results,
            "kb_debug_info": kb_debug_info
        }

    def new_session(self):
        self._log("Creating a new session", 1)
        session_id, session_data = session_manager.new_session(self.current_model)
        self.current_session = session_data
        self.sessions[session_id] = session_data
        self._log(f"New session created with ID: {session_id}", 2)
        return session_id

    def load_session(self, session_id):
        self._log(f"Loading session with ID: {session_id}", 1)
        session_data = session_manager.load_session(session_id)
        if session_data:
            self.current_session = session_data
            self._log("Session loaded successfully", 2)
            return True
        self._log("Session load failed", 2)
        return False

    def delete_session(self, session_id):
        self._log(f"Deleting session with ID: {session_id}", 1)
        if session_manager.delete_session(session_id):
            if session_id in self.sessions:
                del self.sessions[session_id]
            if self.current_session and self.current_session.get("id") == session_id:
                self.new_session()
            self._log("Session deleted successfully", 2)
            return True
        self._log("Session deletion failed", 2)
        return False

    def export_session(self, session_id, file_path):
        self._log(f"Exporting session with ID: {session_id} to file: {file_path}", 1)
        session_data = self.sessions.get(session_id)
        if session_data:
            result = session_manager.export_session(session_data, file_path)
            self._log(f"Session export result: {result}", 2)
            return result
        self._log("Export session: No session data found", 2)
        return False

    def store_message_in_session(self, role, message):
        self._log(f"Storing message in session. Role: {role}, Message: {message}", 2)
        if self.current_session:
            session_manager.store_message_in_session(self.current_session, role, message)
            self._log("Message stored successfully", 3)

    def generate_image_caption(self, image_path):
        self._log(f"Generating image caption for: {image_path}", 1)
        try:
            image = Image.open(image_path)
            self._log(f"Opened image. Mode: {image.mode}", 2)
            if image.mode != "RGB":
                image = image.convert("RGB")
                self._log("Converted image to RGB", 2)
            caption_output = self.image_captioner(image)
            caption = caption_output[0]["generated_text"].strip()
            self._log(f"Generated caption: {caption}", 2)
            return caption
        except Exception as e:
            error_message = f"[Error generating caption: {str(e)}]"
            self._log(error_message, 1)
            return error_message

    def generate_image_text(self, image_path):
        self._log(f"Generating image text for: {image_path}", 1)
        try:
            # Read Tesseract configuration from config.json exclusively.
            if os.path.exists(CONFIG_PATH):
                self._log("Reading configuration file for Tesseract settings", 2)
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    config = json.load(f)
                tesseract_path = config.get("tesseract_path", None)
                tessdata_prefix = config.get("tessdata_prefix", None)
                if tesseract_path is None or tessdata_prefix is None:
                    error_msg = "[Error: Tesseract configuration missing in config.json]"
                    self._log(error_msg, 1)
                    return error_msg
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                self._log(f"Set Tesseract path: {tesseract_path}", 3)
                os.environ["TESSDATA_PREFIX"] = tessdata_prefix
                self._log(f"Set TESSDATA_PREFIX: {tessdata_prefix}", 3)
            else:
                error_msg = "[Error: config.json not found]"
                self._log(error_msg, 1)
                return error_msg

            image = Image.open(image_path)
            self._log("Opened image for OCR", 2)
            gray = image.convert('L')
            self._log("Converted image to grayscale", 3)
            enhancer = ImageEnhance.Contrast(gray)
            enhanced = enhancer.enhance(2)
            self._log("Enhanced image contrast", 3)
            filtered = enhanced.filter(ImageFilter.MedianFilter())
            self._log("Applied median filter", 3)
            ocr_text = pytesseract.image_to_string(filtered)
            ocr_text = ocr_text.strip()
            self._log(f"OCR extracted text: {ocr_text}", 2)
            return ocr_text if ocr_text else "[No text detected]"
        except Exception as e:
            error_message = f"[Error during OCR: {str(e)}]"
            self._log(error_message, 1)
            return error_message
