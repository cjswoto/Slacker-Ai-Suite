#!/usr/bin/env python
"""
OllamaTrainer.py

A production-grade training UI for fine-tuning an open-source LLM using flexible quantization options,
and converting the fine-tuned model for deployment with Ollama.
This application uses ttkbootstrap for a modern Windows-style UI.
"""

import os
import sys
import json
import threading
import subprocess
import logging
import tkinter as tk
from tkinter import filedialog, scrolledtext
import ttkbootstrap as tb
from ttkbootstrap.constants import *

import torch
from torch.utils.data import Dataset
from transformers import (AutoModelForCausalLM, AutoTokenizer, TrainingArguments,
                          Trainer, DataCollatorForLanguageModeling, BitsAndBytesConfig)
from datasets import Dataset as HFDataset

# Attempt to import PEFT and quantization libraries with fallbacks
try:
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
except ImportError:
    LoraConfig = None
    get_peft_model = None
    prepare_model_for_kbit_training = None

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OllamaTrainer")

# Global constant: Directory where the fine-tuned model will be saved
FINE_TUNED_DIR = "./fine-tuned-model"


class TokenizedTextDataset(Dataset):
    def __init__(self, hf_dataset, tokenizer, max_length):
        self.dataset = hf_dataset.map(
            lambda examples: tokenizer(
                examples["text"],
                truncation=True,
                max_length=max_length,
                padding="max_length"
            ),
            batched=True
        )
        self.dataset.set_format(type="torch", columns=["input_ids", "attention_mask"])

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        return self.dataset[idx]


class OllamaTrainerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OllamaTrainer - Fine-Tune and Convert for Ollama")
        self.root.geometry("1200x800")
        self.logger = logger

        self.model_name = tk.StringVar(value="EleutherAI/gpt-neo-125M")
        self.tokenizer = None
        self.model = None

        self.batch_size = tk.IntVar(value=2)
        self.num_epochs = tk.IntVar(value=3)
        self.learning_rate = tk.DoubleVar(value=2e-4)
        self.max_length = tk.IntVar(value=512)

        self.train_file_path = tk.StringVar(value="")

        self.eval_strategy = tk.StringVar(value="no")
        self.eval_split_ratio = tk.DoubleVar(value=0.2)

        self.create_widgets()

    @property
    def device(self):
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def create_widgets(self):
        self.style = tb.Style(theme="darkly")

        main_frame = tb.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        top_frame = tb.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=5)

        model_frame = tb.Labelframe(top_frame, text="Model Selection", bootstyle="info")
        model_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        tb.Label(model_frame, text="Select Base Model:").pack(anchor=tk.W, padx=5, pady=2)
        self.model_dropdown = tb.Combobox(model_frame, textvariable=self.model_name, state="readonly")
        self.model_dropdown['values'] = (
            "EleutherAI/gpt-neo-125M",
            "distilgpt2",
            "gpt2-medium",
            "gpt2-large",
            "gpt2-xl",
            "EleutherAI/gpt-j-6B",
            "Mistralai/Mistral-7B-v0.1",
            "Falcon-7B"
        )
        self.model_dropdown.current(0)
        self.model_dropdown.pack(fill=tk.X, padx=5, pady=5)

        hp_frame = tb.Labelframe(top_frame, text="Training Hyperparameters", bootstyle="warning")
        hp_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        labels = ["Batch Size:", "Epochs:", "Learning Rate:", "Max Seq Length:"]
        vars = [self.batch_size, self.num_epochs, self.learning_rate, self.max_length]
        for i, (label, var) in enumerate(zip(labels, vars)):
            tb.Label(hp_frame, text=label).grid(row=i, column=0, sticky='w', padx=5, pady=2)
            tb.Entry(hp_frame, textvariable=var, width=8).grid(row=i, column=1, padx=5, pady=2)

        eval_frame = tb.Labelframe(top_frame, text="Evaluation Settings", bootstyle="success")
        eval_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        tb.Label(eval_frame, text="Evaluation Strategy:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.eval_strategy_dropdown = tb.Combobox(eval_frame, textvariable=self.eval_strategy,
                                                  values=["no", "epoch", "steps"], state="readonly")
        self.eval_strategy_dropdown.grid(row=0, column=1, padx=5, pady=2)
        tb.Label(eval_frame, text="Validation Split Ratio:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.eval_split_ratio_entry = tb.Entry(eval_frame, textvariable=self.eval_split_ratio, width=8)
        self.eval_split_ratio_entry.grid(row=1, column=1, padx=5, pady=2)

        data_frame = tb.Labelframe(top_frame, text="Training Data", bootstyle="primary")
        data_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        tb.Label(data_frame, text="Training File:").pack(anchor=tk.W, padx=5, pady=2)
        self.data_entry = tb.Entry(data_frame, textvariable=self.train_file_path, width=40)
        self.data_entry.pack(padx=5, pady=2)
        self.browse_button = tb.Button(data_frame, text="Browse...", command=self.browse_file, bootstyle="info")
        self.browse_button.pack(padx=5, pady=2)

        mid_frame = tb.Frame(main_frame)
        mid_frame.pack(fill=tk.X, pady=10)
        self.train_button = tb.Button(mid_frame, text="Fine-Tune Model", command=self.fine_tune_model,
                                      bootstyle="success")
        self.train_button.pack(side=tk.LEFT, padx=10)
        self.convert_button = tb.Button(mid_frame, text="Convert to Ollama Format", command=self.convert_model,
                                        bootstyle="danger")
        self.convert_button.pack(side=tk.LEFT, padx=10)

        log_frame = tb.Labelframe(main_frame, text="Logs", bootstyle="secondary")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_box = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state='disabled', height=15)
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def browse_file(self):
        initial_dir = os.path.abspath(os.path.join(os.getcwd(), "./OllamaDataPrep/output"))
        if not os.path.exists(initial_dir):
            initial_dir = os.getcwd()
        file_path = filedialog.askopenfilename(
            initialdir=initial_dir,
            title="Select Training Data",
            filetypes=[
                ("JSON Lines files", "*.jsonl"),
                ("JSON files", "*.json"),
                ("Text files", "*.txt")
            ])
        if file_path:
            self.train_file_path.set(file_path)
            self.log_message(f"Selected training file: {file_path}")

    def log_message(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)
        self.log_box.configure(state="disabled")
        self.logger.info(message)

    def fine_tune_model(self):
        threading.Thread(target=self._fine_tune_model_worker, daemon=True).start()

    def _fine_tune_model_worker(self):
        train_file = self.train_file_path.get()
        if not train_file or not os.path.exists(train_file):
            self.log_message("Error: Training file not found.")
            return
        self.log_message(f"Loading tokenizer: {self.model_name.get()}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name.get())
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.log_message("Set padding token to end-of-sequence token")
        try:
            self.log_message("Attempting 4-bit quantization with bitsandbytes.")
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True
            )
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name.get(),
                quantization_config=quantization_config,
                device_map="auto"
            )
            if prepare_model_for_kbit_training:
                model = prepare_model_for_kbit_training(model)
        except Exception as e:
            self.log_message(f"4-bit quantization failed: {e}")
            self.log_message("Falling back to standard model loading.")
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name.get(),
                device_map="auto"
            )
        if get_peft_model and LoraConfig:
            try:
                lora_config = LoraConfig(
                    r=16,
                    lora_alpha=32,
                    target_modules=["q_proj", "v_proj"] if "mistral" in self.model_name.get().lower() else None
                )
                model = get_peft_model(model, lora_config)
                self.log_message("LoRA configuration applied successfully.")
            except Exception as e:
                self.log_message(f"LoRA configuration failed: {e}")
        texts = self._load_training_data(train_file)
        self.log_message(f"Dataset loaded with {len(texts)} examples.")
        eval_strategy = self.eval_strategy.get()
        if eval_strategy in ["epoch", "steps"]:
            import random
            random.shuffle(texts)
            split_ratio = self.eval_split_ratio.get()
            split_index = int(len(texts) * (1 - split_ratio))
            train_texts = texts[:split_index]
            eval_texts = texts[split_index:]
            self.log_message(
                f"Automatically split dataset: {len(train_texts)} training examples, {len(eval_texts)} validation examples")
            train_hf_dataset = HFDataset.from_dict({"text": train_texts})
            eval_hf_dataset = HFDataset.from_dict({"text": eval_texts})
            train_dataset = TokenizedTextDataset(train_hf_dataset, self.tokenizer, self.max_length.get())
            eval_dataset = TokenizedTextDataset(eval_hf_dataset, self.tokenizer, self.max_length.get())
        else:
            train_hf_dataset = HFDataset.from_dict({"text": texts})
            train_dataset = TokenizedTextDataset(train_hf_dataset, self.tokenizer, self.max_length.get())
            eval_dataset = None
        training_args = TrainingArguments(
            output_dir=FINE_TUNED_DIR,
            per_device_train_batch_size=self.batch_size.get(),
            num_train_epochs=self.num_epochs.get(),
            learning_rate=self.learning_rate.get(),
            fp16=torch.cuda.is_available(),
            save_strategy="epoch",
            evaluation_strategy=self.eval_strategy.get(),
            logging_steps=50,
            overwrite_output_dir=True
        )
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=DataCollatorForLanguageModeling(self.tokenizer, mlm=False)
        )
        try:
            trainer.train()
            model.save_pretrained(FINE_TUNED_DIR)
            self.tokenizer.save_pretrained(FINE_TUNED_DIR)
            self.log_message("Fine-tuning completed and model saved.")
        except Exception as e:
            self.log_message(f"Training failed: {e}")

    def _load_training_data(self, train_file):
        texts = []
        try:
            ext = train_file.split('.')[-1].lower()
            with open(train_file, "r", encoding="utf-8") as f:
                if ext == "jsonl":
                    for line in f:
                        line = line.strip()
                        if line:
                            obj = json.loads(line)
                            if "text" in obj:
                                texts.append(obj["text"])
                elif ext == "json":
                    data = json.load(f)
                    if isinstance(data, list):
                        for obj in data:
                            if isinstance(obj, dict) and "text" in obj:
                                texts.append(obj["text"])
                else:
                    texts = [f.read()]
        except Exception as e:
            self.log_message(f"Error loading training data: {e}")
        return texts

    def convert_model(self):
        threading.Thread(target=self._convert_model_worker, daemon=True).start()

    def _convert_model_worker(self):
        output_file = os.path.join(os.getcwd(), "fine-tuned-model.gguf")
        try:
            subprocess.run([
                sys.executable, "convert_hf_to_gguf.py",
                "--model-input", FINE_TUNED_DIR,
                "--model-output", output_file
            ], check=True)
            self.log_message(f"Model successfully converted to {output_file}")
        except Exception as e:
            self.log_message(f"Model conversion failed: {e}")


if __name__ == "__main__":
    root = tb.Window(themename="darkly")
    app = OllamaTrainerApp(root)
    root.mainloop()
