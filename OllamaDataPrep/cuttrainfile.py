#!/usr/bin/env python
"""
PDF to Training Dataset Generator

This script provides a GUI interface (using ttkbootstrap) that lets you:
  • Browse and select a PDF document.
  • Choose a local AI model (via Ollama) from a dropdown.
  • Generate a training dataset by extracting the PDF text and sending a prompt
    to the selected AI model.
  • Save the generated dataset as a JSON file.

Before running, ensure:
  - PyPDF2 and ttkbootstrap are installed (pip install PyPDF2 ttkbootstrap).
  - Ollama is installed locally and the desired model is available.
"""

import os
import sys
import subprocess
import threading
import logging
import tkinter as tk
from tkinter import filedialog, scrolledtext
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import PyPDF2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PDFDatasetGenerator")

class PDFDatasetGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF to Training Dataset Generator")
        self.root.geometry("1000x600")
        self.logger = logger

        # Variables for the GUI
        self.pdf_file_path = tk.StringVar(value="")
        self.model_name = tk.StringVar(value="local-model-1")
        self.output_file_path = tk.StringVar(value="training_dataset.json")
        self.max_chars = tk.IntVar(value=10000)

        self.create_widgets()

    def create_widgets(self):
        self.style = tb.Style(theme="darkly")

        main_frame = tb.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top frame for file and model selection
        top_frame = tb.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=5)

        # PDF File Selection
        pdf_frame = tb.Labelframe(top_frame, text="PDF Document", bootstyle="primary")
        pdf_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        tb.Label(pdf_frame, text="Select PDF File:").pack(anchor=tk.W, padx=5, pady=2)
        pdf_entry = tb.Entry(pdf_frame, textvariable=self.pdf_file_path, width=40)
        pdf_entry.pack(padx=5, pady=2)
        pdf_browse = tb.Button(pdf_frame, text="Browse...", command=self.browse_pdf, bootstyle="info")
        pdf_browse.pack(padx=5, pady=2)

        # Model selection
        model_frame = tb.Labelframe(top_frame, text="Local AI Model (Ollama)", bootstyle="info")
        model_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        tb.Label(model_frame, text="Select Model:").pack(anchor=tk.W, padx=5, pady=2)
        self.model_dropdown = tb.Combobox(model_frame, textvariable=self.model_name, state="readonly")
        self.model_dropdown['values'] = (
            "local-model-1",
            "local-model-2",
            "local-model-3"
        )
        self.model_dropdown.current(0)
        self.model_dropdown.pack(fill=tk.X, padx=5, pady=5)

        # Output file selection
        output_frame = tb.Labelframe(top_frame, text="Output Settings", bootstyle="warning")
        output_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        tb.Label(output_frame, text="Output File:").pack(anchor=tk.W, padx=5, pady=2)
        output_entry = tb.Entry(output_frame, textvariable=self.output_file_path, width=30)
        output_entry.pack(padx=5, pady=2)
        tb.Label(output_frame, text="Max Characters to Extract:").pack(anchor=tk.W, padx=5, pady=2)
        tb.Entry(output_frame, textvariable=self.max_chars, width=10).pack(padx=5, pady=2)

        # Middle frame for the generate button
        mid_frame = tb.Frame(main_frame)
        mid_frame.pack(fill=tk.X, pady=10)
        generate_button = tb.Button(mid_frame, text="Generate Training Dataset", command=self.generate_dataset, bootstyle="success")
        generate_button.pack(side=tk.LEFT, padx=10)

        # Log box for status messages
        log_frame = tb.Labelframe(main_frame, text="Logs", bootstyle="secondary")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_box = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state='disabled', height=15)
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def browse_pdf(self):
        file_path = filedialog.askopenfilename(
            initialdir=os.getcwd(),
            title="Select PDF Document",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if file_path:
            self.pdf_file_path.set(file_path)
            self.log_message(f"Selected PDF file: {file_path}")

    def log_message(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)
        self.log_box.configure(state="disabled")
        self.logger.info(message)

    def generate_dataset(self):
        threading.Thread(target=self._generate_dataset_worker, daemon=True).start()

    def _generate_dataset_worker(self):
        pdf_path = self.pdf_file_path.get()
        model = self.model_name.get()
        output_path = self.output_file_path.get()
        max_chars = self.max_chars.get()

        if not os.path.exists(pdf_path):
            self.log_message("Error: PDF file not found.")
            return

        self.log_message("Extracting text from PDF...")
        document_text = self.extract_text_from_pdf(pdf_path, max_chars)
        if not document_text:
            self.log_message("Error: No text extracted from the PDF.")
            return

        # Construct a prompt for the AI to generate a training dataset
        prompt = (
            "Based on the following document text, generate a training dataset for fine-tuning a language model. "
            "The dataset should be in JSON format and include examples that capture the key themes, principles, and ideas "
            "from the document.\n\nDocument Text:\n" + document_text
        )
        self.log_message("Calling Ollama AI model '{}'...".format(model))
        ai_response = self.run_ollama(model, prompt)

        if not ai_response:
            self.log_message("Error: No response from the AI model.")
            return

        try:
            with open(output_path, "w", encoding="utf-8") as out_file:
                out_file.write(ai_response)
            self.log_message("Training dataset saved to '{}'.".format(output_path))
        except Exception as e:
            self.log_message(f"Error writing output file: {e}")

    def extract_text_from_pdf(self, pdf_path, max_length=None):
        text = ""
        try:
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
                        if max_length and len(text) >= max_length:
                            text = text[:max_length]
                            break
        except Exception as e:
            self.log_message(f"Error reading PDF: {e}")
        return text

    def run_ollama(self, model, prompt):
        # Use the Ollama CLI to call the selected model with the prompt
        command = ["ollama", "run", model, "-p", prompt]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            self.log_message("Received response from Ollama.")
            return result.stdout
        except subprocess.CalledProcessError as e:
            self.log_message(f"Error calling Ollama: {e}")
            return None

if __name__ == "__main__":
    root = tb.Window(themename="darkly")
    app = PDFDatasetGeneratorApp(root)
    root.mainloop()
