import tkinter as tk
from tkinter import scrolledtext, ttk
import threading
import queue
import logging
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments, DataCollatorForLanguageModeling
from datasets import load_dataset

class AILogic:
    def __init__(self, logger, model_choice="GPT-Neo-125M"):
        self.logger = logger
        self.models = {
            "GPT-Neo-125M": "EleutherAI/gpt-neo-125M",
            "DistilGPT-2": "distilgpt2",
            "GPT-2 Medium": "gpt2-medium",
            "GPT-2 Large": "gpt2-large",
            "GPT-2 XL": "gpt2-xl",
            "GPT-J-6B": "EleutherAI/gpt-j-6B",
            "GPT-NeoX-20B": "EleutherAI/gpt-neox-20b",
            "T5 Small": "t5-small",
            "T5 Base": "t5-base",
            "T5 Large": "t5-large",
            "Fine-Tuned Model": "./fine-tuned-model"  # Add the fine-tuned model here
        }
        self.model_name = self.models.get(model_choice, "EleutherAI/gpt-neo-125M")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.load_model_and_tokenizer()
        self.fine_tuning_data = []

    def load_model_and_tokenizer(self):
        try:
            self.logger.info(f"Loading tokenizer for model {self.model_name}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.logger.info("Tokenizer loaded successfully.")

            self.logger.info(f"Loading model {self.model_name}...")
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name).to(self.device)
            self.logger.info("Model loaded successfully.")
        except Exception as e:
            self.logger.error(f"Error loading model or tokenizer: {e}")
            exit(1)

    def generate_text(self, prompt, max_length=100, temperature=0.7, top_p=0.9):
        self.logger.info(f"Generating text for prompt: {prompt} with temperature={temperature}, top_p={top_p}")
        if not prompt.strip():
            return "Please enter a valid input."
        try:
            input_ids = self.tokenizer.encode(prompt, return_tensors='pt').to(self.device)
            pad_token_id = self.tokenizer.eos_token_id
            attention_mask = input_ids.ne(pad_token_id).long()
            output = self.model.generate(
                input_ids,
                max_length=max_length,
                num_return_sequences=1,
                pad_token_id=pad_token_id,
                attention_mask=attention_mask,
                temperature=temperature,
                top_p=top_p,
                do_sample=True
            )
            output_text = self.tokenizer.decode(output[0], skip_special_tokens=True)
            self.logger.info(f"Generated text: {output_text}")
            return output_text
        except Exception as e:
            self.logger.error(f"Error generating text: {e}")
            return "Error generating text."

    def provide_feedback(self, selected_text, feedback):
        self.fine_tuning_data.append(f"PROMPT: {selected_text}\nRESPONSE: {feedback}\n")

    def fine_tune_model(self):
        self.logger.info("Starting fine-tuning...")
        fine_tuning_file_path = "fine_tuning_data.json"

        # Load the dataset
        try:
            dataset = load_dataset('text', data_files={'train': fine_tuning_file_path})
            dataset = dataset['train'].train_test_split(test_size=0.1)
            self.logger.info(f"Dataset loaded with {len(dataset['train'])} training examples and {len(dataset['test'])} testing examples.")
        except Exception as e:
            self.logger.error(f"Error loading dataset: {e}")
            return

        # Tokenize the dataset
        def tokenize_function(examples):
            return self.tokenizer(examples['text'], truncation=True, max_length=512)

        try:
            tokenized_datasets = dataset.map(tokenize_function, batched=True)
            self.logger.info("Dataset tokenized successfully.")
        except Exception as e:
            self.logger.error(f"Error tokenizing dataset: {e}")
            return

        # Set the format of the dataset
        tokenized_datasets.set_format(type='torch', columns=['input_ids', 'attention_mask'])

        # Data collator
        data_collator = DataCollatorForLanguageModeling(tokenizer=self.tokenizer, mlm=False)

        # Training arguments
        training_args = TrainingArguments(
            output_dir="./fine-tuned-model",
            overwrite_output_dir=True,
            num_train_epochs=1,
            per_device_train_batch_size=1,
            save_steps=10_000,
            save_total_limit=2,
            evaluation_strategy="epoch",
            logging_dir='./logs',
            logging_steps=10,
            fp16=True if torch.cuda.is_available() else False,
        )

        # Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            data_collator=data_collator,
            train_dataset=tokenized_datasets['train'],
            eval_dataset=tokenized_datasets['test'],
        )

        # Train model
        try:
            trainer.train()
            self.logger.info("Fine-tuning completed successfully.")

            # Load the fine-tuned model after training
            self.logger.info("Loading the fine-tuned model...")
            self.model = AutoModelForCausalLM.from_pretrained("./fine-tuned-model").to(self.device)
            self.logger.info("Fine-tuned model loaded and ready to use.")
        except Exception as e:
            self.logger.error(f"Error during training: {e}")

class Job:
    def __init__(self, query, temp_min, temp_max, temp_step, top_p_min, top_p_max, top_p_step, max_length):
        self.query = query
        self.temp_min = temp_min
        self.temp_max = temp_max
        self.temp_step = temp_step
        self.top_p_min = top_p_min
        self.top_p_max = top_p_max
        self.top_p_step = top_p_step
        self.max_length = max_length
        self.status = "Queued"

    def __str__(self):
        return f"Prompt: {self.query}, Temp: {self.temp_min}-{self.temp_max} (step {self.temp_step}), Top-p: {self.top_p_min}-{self.top_p_max} (step {self.top_p_step}), Max Length: {self.max_length}, Status: {self.status}"

def create_tooltip(widget, text):
    toolTip = tk.Toplevel(widget)
    toolTip.wm_overrideredirect(True)
    toolTip.wm_geometry("+0+0")
    label = tk.Label(toolTip, text=text, justify='left', background="#ffffff", relief='solid', borderwidth=1, wraplength=300)
    label.pack(ipadx=1)
    toolTip.withdraw()

    def enter(event):
        x = event.widget.winfo_rootx() + 20
        y = event.widget.winfo_rooty() + 20
        toolTip.wm_geometry(f"+{x}+{y}")
        toolTip.deiconify()

    def leave(event):
        toolTip.withdraw()

    widget.bind("<Enter>", enter)
    widget.bind("<Leave>", leave)

def submit_query(ui):
    query = ui.user_input.get()
    if not query.strip():
        ui.chat_box.insert(tk.END, "Please enter a valid input.\n")
        return

    selected_model = ui.model_var.get()  # Get the selected model from the dropdown
    if selected_model != ui.logic.model_name:
        ui.logger.info(f"Switching model to {selected_model}...")
        ui.logic.model_name = selected_model
        ui.logic.load_model_and_tokenizer()

    temp_min = float(ui.temp_min_input.get())
    temp_max = float(ui.temp_max_input.get())
    temp_step = float(ui.temp_step_input.get())
    top_p_min = float(ui.top_p_min_input.get())
    top_p_max = float(ui.top_p_max_input.get())
    top_p_step = float(ui.top_p_step_input.get())
    max_length = int(ui.max_length_input.get())

    job_count = 0
    temp = temp_min
    while temp <= temp_max:
        top_p = top_p_min
        while top_p <= top_p_max:
            job = Job(query, temp, temp_max, temp_step, top_p, top_p_max, top_p_step, max_length)
            ui.jobs.append(job)
            ui.job_queue.put(job)
            job_count += 1
            top_p = round(top_p + top_p_step, 10)
        temp = round(temp + temp_step, 10)

    batch_info = f"Batch: {job_count} jobs, Temp Range: {temp_min}-{temp_max}, Top-p Range: {top_p_min}-{top_p_max}"
    ui.logger.info(batch_info)
    ui.job_listbox.insert(tk.END, batch_info)
    update_job_listbox(ui)

    ui.user_input.set("")

def update_job_listbox(ui):
    ui.job_listbox.delete(0, tk.END)
    for job in ui.jobs:
        ui.job_listbox.insert(tk.END, str(job))

def process_jobs(ui):
    while True:
        job = ui.job_queue.get()
        job.status = "Running"
        update_job_listbox(ui)

        temp = job.temp_min
        while temp <= job.temp_max:
            top_p = job.top_p_min
            while top_p <= job.top_p_max:
                if ui.cancel_pending:
                    job.status = "Cancelled"
                    update_job_listbox(ui)
                    ui.job_queue.task_done()
                    return

                response = ui.logic.generate_text(job.query, max_length=job.max_length, temperature=temp, top_p=top_p)
                with open("output.txt", "a", encoding="utf-8") as output_file:
                    output_file.write(f"Query: {job.query}\n")
                    output_file.write(f"Temperature: {temp}, Top-p: {top_p}\nAI: {response}\n\n")
                ui.chat_box.insert(tk.END, f"Temperature: {temp}, Top-p: {top_p}\nAI: {response}\n\n")
                ui.chat_box.update_idletasks()
                top_p = round(top_p + job.top_p_step, 10)
            temp = round(temp + job.temp_step, 10)

        job.status = "Complete"
        update_job_listbox(ui)
        ui.job_queue.task_done()

def cancel_all_jobs(ui):
    ui.cancel_pending = True
    ui.job_queue.queue.clear()
    for job in ui.jobs:
        if job.status == "Queued":
            job.status = "Cancelled"
    update_job_listbox(ui)
    ui.cancel_pending = False

def provide_feedback(ui):
    feedback = ui.feedback_input.get()
    try:
        selected_text = ui.chat_box.get(tk.SEL_FIRST, tk.SEL_LAST)
        ui.chat_box.insert(tk.END, "Feedback: " + feedback + "\n")
        ui.logic.provide_feedback(selected_text, feedback)
        ui.feedback_input.set("")
    except tk.TclError:
        ui.chat_box.insert(tk.END, "Feedback: Please select the AI response text before providing feedback.\n")

def fine_tune_model(ui):
    ui.logic.fine_tune_model()

def show_help(root):
    help_window = tk.Toplevel(root)
    help_window.title("Help")
    help_window.geometry("600x400")

    help_text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD)
    help_text_widget.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    with open("help_wiki.txt", "r") as file:
        help_text = file.read()

    help_text_widget.insert(tk.END, help_text)
    help_text_widget.configure(state='disabled')

class AIUI:
    def __init__(self, root, logger):
        self.root = root
        self.logger = logger
        self.logic = AILogic(self.logger)
        self.job_queue = queue.Queue()
        self.jobs = []
        self.cancel_pending = False
        self.prompt_response_pairs = []

        self.create_widgets()
        self.create_tooltips()

        self.worker_thread = threading.Thread(target=process_jobs, args=(self,))
        self.worker_thread.daemon = True
        self.worker_thread.start()

    def create_widgets(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=1)

        canvas = tk.Canvas(main_frame)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        self.scrollable_frame = tk.Frame(canvas)
        self.scrollable_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        for i in range(15):
            self.scrollable_frame.rowconfigure(i, weight=1)
        self.scrollable_frame.columnconfigure(0, weight=1)

        tk.Label(self.scrollable_frame, text="Prompt Input:").grid(row=0, column=0, sticky='nsew')
        self.user_input = tk.StringVar()
        self.user_input_entry = tk.Entry(self.scrollable_frame, textvariable=self.user_input, width=80)
        self.user_input_entry.grid(row=1, column=0, rowspan=3, padx=10, pady=10, sticky='nsew')

        tk.Label(self.scrollable_frame, text="Model:").grid(row=4, column=0, sticky='nsew')
        self.model_var = tk.StringVar()
        self.model_dropdown = ttk.Combobox(self.scrollable_frame, textvariable=self.model_var)
        self.model_dropdown['values'] = (
            "EleutherAI/gpt-neo-125M",
            "distilgpt2",
            "GPT-2 Medium",
            "GPT-2 Large",
            "GPT-2 XL",
            "GPT-J-6B",
            "GPT-NeoX-20B",
            "T5 Small",
            "T5 Base",
            "T5 Large",
            "Fine-Tuned Model"  # Add the fine-tuned model to the dropdown
        )
        self.model_dropdown.current(0)  # Default selection
        self.model_dropdown.grid(row=5, column=0, sticky='nsew')

        tk.Label(self.scrollable_frame, text="Temperature Range:").grid(row=6, column=0, sticky='nsew')
        self.temp_min_input = tk.Spinbox(self.scrollable_frame, from_=0.1, to=1.0, increment=0.1)
        self.temp_min_input.delete(0, "end")
        self.temp_min_input.insert(0, "0.1")
        self.temp_min_input.grid(row=7, column=0, sticky='nsew')

        self.temp_max_input = tk.Spinbox(self.scrollable_frame, from_=0.1, to=1.0, increment=0.1)
        self.temp_max_input.delete(0, "end")
        self.temp_max_input.insert(0, "1.0")
        self.temp_max_input.grid(row=8, column=0, sticky='nsew')

        self.temp_step_input = tk.Spinbox(self.scrollable_frame, from_=0.1, to=1.0, increment=0.1)
        self.temp_step_input.delete(0, "end")
        self.temp_step_input.insert(0, "0.1")
        self.temp_step_input.grid(row=9, column=0, sticky='nsew')

        tk.Label(self.scrollable_frame, text="Top-p Range:").grid(row=10, column=0, sticky='nsew')
        self.top_p_min_input = tk.Spinbox(self.scrollable_frame, from_=0.1, to=1.0, increment=0.1)
        self.top_p_min_input.delete(0, "end")
        self.top_p_min_input.insert(0, "0.1")
        self.top_p_min_input.grid(row=11, column=0, sticky='nsew')

        self.top_p_max_input = tk.Spinbox(self.scrollable_frame, from_=0.1, to=1.0, increment=0.1)
        self.top_p_max_input.delete(0, "end")
        self.top_p_max_input.insert(0, "1.0")
        self.top_p_max_input.grid(row=12, column=0, sticky='nsew')

        self.top_p_step_input = tk.Spinbox(self.scrollable_frame, from_=0.1, to=1.0, increment=0.1)
        self.top_p_step_input.delete(0, "end")
        self.top_p_step_input.insert(0, "0.1")
        self.top_p_step_input.grid(row=13, column=0, sticky='nsew')

        tk.Label(self.scrollable_frame, text="Max Length:").grid(row=14, column=0, sticky='nsew')
        self.max_length_input = tk.Spinbox(self.scrollable_frame, from_=1, to=1024, increment=1)
        self.max_length_input.delete(0, "end")
        self.max_length_input.insert(0, "100")
        self.max_length_input.grid(row=15, column=0, sticky='nsew')

        self.submit_button = tk.Button(self.scrollable_frame, text="Submit", command=lambda: submit_query(self))
        self.submit_button.grid(row=16, column=0, pady=5, sticky='nsew')

        tk.Label(self.scrollable_frame, text="Response:").grid(row=17, column=0, sticky='nsew')
        self.chat_box = scrolledtext.ScrolledText(self.scrollable_frame, wrap=tk.WORD)
        self.chat_box.grid(row=18, column=0, padx=10, pady=10, sticky='nsew')

        tk.Label(self.scrollable_frame, text="Logging:").grid(row=19, column=0, sticky='nsew')
        self.log_box = scrolledtext.ScrolledText(self.scrollable_frame, wrap=tk.WORD, state='disabled')
        self.log_box.grid(row=20, column=0, padx=10, pady=10, sticky='nsew')

        tk.Label(self.scrollable_frame, text="Job Queue:").grid(row=21, column=0, sticky='nsew')
        self.job_listbox = tk.Listbox(self.scrollable_frame)
        self.job_listbox.grid(row=22, column=0, padx=10, pady=10, sticky='nsew')

        self.cancel_button = tk.Button(self.scrollable_frame, text="Cancel All Jobs", command=lambda: cancel_all_jobs(self))
        self.cancel_button.grid(row=23, column=0, pady=5, sticky='nsew')

        tk.Label(self.scrollable_frame, text="Prompt-Response Pairs:").grid(row=24, column=0, sticky='nsew')
        self.pair_listbox = tk.Listbox(self.scrollable_frame)
        self.pair_listbox.grid(row=25, column=0, padx=10, pady=10, sticky='nsew')

        tk.Label(self.scrollable_frame, text="Feedback:").grid(row=26, column=0, sticky='nsew')
        self.feedback_input = tk.StringVar()
        self.feedback_input_entry = tk.Entry(self.scrollable_frame, textvariable=self.feedback_input, width=80)
        self.feedback_input_entry.grid(row=27, column=0, padx=10, pady=10, sticky='nsew')

        self.feedback_button = tk.Button(self.scrollable_frame, text="Provide Feedback", command=lambda: provide_feedback(self))
        self.feedback_button.grid(row=28, column=0, pady=5, sticky='nsew')

        self.fine_tune_button = tk.Button(self.scrollable_frame, text="Fine-Tune Model", command=lambda: fine_tune_model(self))
        self.fine_tune_button.grid(row=29, column=0, pady=5, sticky='nsew')

    def create_tooltips(self):
        create_tooltip(self.user_input_entry, "Enter your prompt here.")
        create_tooltip(self.model_dropdown, "Select the model to use.")
        create_tooltip(self.temp_min_input, "Minimum temperature value for the range. Lower values make the output more focused and deterministic.")
        create_tooltip(self.temp_max_input, "Maximum temperature value for the range. Higher values make the output more random and creative.")
        create_tooltip(self.temp_step_input, "Step size for the temperature range.")
        create_tooltip(self.top_p_min_input, "Minimum top-p value for the range. Lower values mean less diversity.")
        create_tooltip(self.top_p_max_input, "Maximum top-p value for the range. Higher values mean more diversity.")
        create_tooltip(self.top_p_step_input, "Step size for the top-p range.")
        create_tooltip(self.max_length_input, "The maximum number of tokens to generate. Example: 100")
        create_tooltip(self.feedback_input_entry, "Enter feedback about the AI's response here to help fine-tune and improve the model.")
        create_tooltip(self.fine_tune_button, "Use the collected feedback to fine-tune the model and improve its responses.")

    @staticmethod
    def show_help(root):
        show_help(root)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    root = tk.Tk()
    root.title("AI Assistant")
    root.geometry("800x600")
    app = AIUI(root, logger)
    root.mainloop()
