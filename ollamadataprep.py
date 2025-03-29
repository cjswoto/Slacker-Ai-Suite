#!/usr/bin/env python
"""
OllamaDataPrep.py

Modern GUI app to convert raw documents into structured datasets for OllamaTrainer.
"""

import os
import json
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import pandas as pd
from datasets import Dataset
from pdfminer.high_level import extract_text
import docx
import textract


class OllamaDataPrep:
    def __init__(self, root):
        self.root = root
        self.root.title("OllamaDataPrep - Prepare Data for OllamaTrainer")
        self.root.geometry("800x600")

        self.files = []
        self.data_type = tk.StringVar(value="instruction")
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)

        self.create_widgets()

    def create_widgets(self):
        tb.Label(self.root, text="Select Raw Data Files:", font=("Segoe UI", 12)).pack(pady=10)

        self.file_listbox = tk.Listbox(self.root, height=8)
        self.file_listbox.pack(fill=X, padx=20)

        select_btn = tb.Button(self.root, text="Add Files", command=self.add_files, bootstyle="info")
        select_btn.pack(pady=5)

        data_type_frame = tb.Frame(self.root)
        data_type_frame.pack(pady=5)

        tb.Radiobutton(data_type_frame, text="Instruction (Q&A)", variable=self.data_type, value="instruction").pack(
            side=LEFT, padx=10)
        tb.Radiobutton(data_type_frame, text="Plain Text", variable=self.data_type, value="plaintext").pack(side=LEFT,
                                                                                                            padx=10)

        convert_btn = tb.Button(self.root, text="Convert & Export Dataset", command=self.convert_files,
                                bootstyle="success")
        convert_btn.pack(pady=10)

        tb.Label(self.root, text="Logs & Status:", font=("Segoe UI", 12)).pack(pady=5)
        self.log_box = scrolledtext.ScrolledText(self.root, state='disabled', height=15)
        self.log_box.pack(fill=BOTH, expand=True, padx=10, pady=5)

    def add_files(self):
        file_paths = filedialog.askopenfilenames(title="Select Raw Data Files",
                                                 filetypes=[("All Supported", "*.txt *.pdf *.docx *.csv *.xlsx"),
                                                            ("All Files", "*.*")])
        for path in file_paths:
            if path not in self.files:
                self.files.append(path)
                self.file_listbox.insert(END, os.path.basename(path))
                self.log(f"Added file: {path}")

    def convert_files(self):
        if not self.files:
            messagebox.showerror("Error", "No files selected.")
            return

        dataset = []
        for file in self.files:
            text = self.extract_text(file)
            if self.data_type.get() == "instruction":
                pairs = self.extract_instruction_pairs(text)
                dataset.extend(pairs)
            else:
                segments = self.segment_plain_text(text)
                dataset.extend([{"text": seg} for seg in segments])

        output_file = os.path.join(self.output_dir, "dataset.jsonl")
        with open(output_file, "w", encoding="utf-8") as f:
            for entry in dataset:
                f.write(json.dumps(entry) + "\n")

        self.log(f"Dataset exported successfully: {output_file}")
        messagebox.showinfo("Completed", f"Dataset saved to {output_file}")

    def extract_text(self, file):
        try:
            if file.endswith(".pdf"):
                text = extract_text(file)
            elif file.endswith(".docx"):
                doc = docx.Document(file)
                text = "\n".join([para.text for para in doc.paragraphs])
            elif file.endswith((".txt", ".csv")):
                with open(file, encoding="utf-8") as f:
                    text = f.read()
            elif file.endswith(".xlsx"):
                df = pd.read_excel(file, engine='openpyxl')
                text = df.to_string()
            else:
                text = textract.process(file).decode('utf-8')
            self.log(f"Extracted text from {file}")
            return text
        except Exception as e:
            self.log(f"Error extracting {file}: {e}")
            return ""

    def extract_instruction_pairs(self, text):
        pairs = []
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for i in range(0, len(lines) - 1, 2):
            pairs.append({
                "instruction": lines[i],
                "response": lines[i + 1]
            })
        self.log(f"Extracted {len(pairs)} instruction pairs.")
        return pairs

    def segment_plain_text(self, text, max_chars=1000):
        segments = []
        while len(text) > max_chars:
            split_idx = text.rfind(".", 0, max_chars) + 1
            if split_idx <= 0:
                split_idx = max_chars
            segments.append(text[:split_idx].strip())
            text = text[split_idx:].strip()
        if text:
            segments.append(text.strip())
        self.log(f"Segmented text into {len(segments)} segments.")
        return segments

    def log(self, message):
        self.log_box.config(state='normal')
        self.log_box.insert(END, message + "\n")
        self.log_box.see(END)
        self.log_box.config(state='disabled')


if __name__ == "__main__":
    root = tb.Window(themename="darkly")
    app = OllamaDataPrep(root)
    root.mainloop()
