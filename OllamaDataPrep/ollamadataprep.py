# ollamadataprep.py

import os
import json
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog, ttk
import time

class OllamaDataPrep:
    def __init__(self, root):
        self.root = root
        self.root.title("Ollama Data Prep")
        self.root.geometry("1200x700")
        self.root.configure(bg="#2b2b2b")

        self.files = []
        self.mode = tk.StringVar(value="instruction")
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        center_frame = ttk.Frame(main_frame)
        center_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        right_frame = ttk.LabelFrame(main_frame, text="File Viewer")
        right_frame.pack(side="right", fill="both", expand=True)

        top_controls = ttk.Frame(left_frame)
        top_controls.pack(fill="x")

        ttk.Button(top_controls, text="Add Files", command=self.add_files).pack(side="left", padx=5)
        ttk.Button(top_controls, text="Clear Files", command=self.clear_files).pack(side="left", padx=5)
        ttk.Button(top_controls, text="Convert & Export Dataset", command=self.export_dataset).pack(side="left", padx=5)

        self.file_listbox = tk.Listbox(left_frame, height=10, bg="#2b2b2b", fg="#ffffff", selectbackground="#007acc")
        self.file_listbox.pack(padx=5, pady=5, fill="both", expand=True)

        mode_frame = ttk.LabelFrame(left_frame, text="Conversion Mode")
        mode_frame.pack(fill="x", pady=(5, 5))

        ttk.Radiobutton(mode_frame, text="Instruction (Q&A)", variable=self.mode, value="instruction").pack(anchor="w", padx=5)
        ttk.Radiobutton(mode_frame, text="Plain Text", variable=self.mode, value="plain").pack(anchor="w", padx=5)
        ttk.Radiobutton(mode_frame, text="SQuAD JSON File", variable=self.mode, value="squad").pack(anchor="w", padx=5)

        output_frame = ttk.LabelFrame(center_frame, text="Output Folder (OllamaDataPrep/output/)")
        output_frame.pack(fill="both", expand=True)

        self.output_listbox = tk.Listbox(output_frame, height=15, bg="#2b2b2b", fg="#ffffff", selectbackground="#007acc")
        self.output_listbox.pack(fill="both", expand=False, padx=5, pady=5)
        self.output_listbox.bind("<<ListboxSelect>>", self.show_output_metadata)

        remove_btn = ttk.Button(output_frame, text="Remove Selected File", command=self.remove_output_file)
        remove_btn.pack(pady=5)

        self.metadata_text = tk.Text(output_frame, height=8, bg="#2b2b2b", fg="#00ff00", state="disabled")
        self.metadata_text.pack(fill="x", padx=5, pady=(0, 5))

        viewer_frame = ttk.Frame(right_frame)
        viewer_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.viewer_text = tk.Text(viewer_frame, bg="#1e1e1e", fg="#ffffff", wrap="word")
        self.viewer_text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(viewer_frame, orient="vertical", command=self.viewer_text.yview)
        scrollbar.pack(side="right", fill="y")

        self.viewer_text.configure(yscrollcommand=scrollbar.set, state="disabled")

        self.refresh_file_list()
        self.refresh_output_list()

    def add_files(self):
        selected = filedialog.askopenfilenames(filetypes=[("Text/JSON Files", "*.txt *.json")])
        if selected:
            self.files.extend(selected)
            self.refresh_file_list()

    def clear_files(self):
        self.files = []
        self.refresh_file_list()

    def refresh_file_list(self):
        self.file_listbox.delete(0, tk.END)
        for f in self.files:
            self.file_listbox.insert(tk.END, os.path.basename(f))

    def export_dataset(self):
        if not self.files:
            messagebox.showerror("Error", "No files selected.")
            return

        filename = simpledialog.askstring("Export Dataset", "Enter output filename (e.g., dataset.jsonl):", initialvalue="dataset.jsonl")
        if not filename:
            return

        if not filename.lower().endswith(".jsonl"):
            filename += ".jsonl"

        output_dir = os.path.join(os.getcwd(), "OllamaDataPrep", "output")
        os.makedirs(output_dir, exist_ok=True)
        save_path = os.path.join(output_dir, filename)

        all_records = []

        for file_path in self.files:
            try:
                if self.mode.get() == "instruction":
                    records = self.extract_instruction_pairs(file_path)
                elif self.mode.get() == "plain":
                    records = self.extract_plain_text(file_path)
                elif self.mode.get() == "squad":
                    records = self.extract_squad_pairs(file_path)
                else:
                    records = []
                all_records.extend(records)
            except Exception as e:
                print(f"Failed to process {file_path}: {e}")

        if not all_records:
            messagebox.showerror("Error", "No data extracted from selected files.")
            return

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                for record in all_records:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")

            meta = {
                "filename": filename,
                "format": self.mode.get(),
                "record_count": len(all_records),
                "created": time.ctime()
            }
            with open(save_path + ".meta.json", "w", encoding="utf-8") as mf:
                json.dump(meta, mf, indent=2)

            messagebox.showinfo("Success", f"Dataset exported to:\n{save_path}")
            self.refresh_output_list()
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def refresh_output_list(self):
        output_dir = os.path.join(os.getcwd(), "OllamaDataPrep", "output")
        os.makedirs(output_dir, exist_ok=True)

        self.output_listbox.delete(0, tk.END)
        for file in sorted(os.listdir(output_dir)):
            if file.endswith(".jsonl") and not file.endswith(".meta.json"):
                self.output_listbox.insert(tk.END, file)

    def show_output_metadata(self, event=None):
        selection = self.output_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        filename = self.output_listbox.get(idx)
        full_path = os.path.join(os.getcwd(), "OllamaDataPrep", "output", filename)
        meta_path = full_path + ".meta.json"

        info = os.stat(full_path)
        size_kb = info.st_size / 1024
        created = time.ctime(info.st_ctime)

        metadata_text = f"Filename: {filename}\n"
        metadata_text += f"Size: {size_kb:.2f} KB\n"
        metadata_text += f"Created: {created}\n"

        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as mf:
                    meta = json.load(mf)
                metadata_text += f"Records: {meta.get('record_count', '?')}\n"
                mode = meta.get("format", "?")
                readable_mode = {
                    "instruction": "Instruction (Q&A)",
                    "plain": "Plain Text",
                    "squad": "SQuAD JSON File"
                }.get(mode, mode)
                metadata_text += f"Format: {readable_mode}\n"
            except:
                metadata_text += f"Records: ?\nFormat: Unknown\n"
        else:
            metadata_text += f"Records: ?\nFormat: Unknown\n"

        self.metadata_text.configure(state="normal")
        self.metadata_text.delete("1.0", tk.END)
        self.metadata_text.insert(tk.END, metadata_text)
        self.metadata_text.configure(state="disabled")

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.viewer_text.configure(state="normal")
            self.viewer_text.delete("1.0", tk.END)
            self.viewer_text.insert(tk.END, content)
            self.viewer_text.configure(state="disabled")
        except Exception as e:
            self.viewer_text.configure(state="normal")
            self.viewer_text.delete("1.0", tk.END)
            self.viewer_text.insert(tk.END, f"Error reading file: {e}")
            self.viewer_text.configure(state="disabled")

    def remove_output_file(self):
        selection = self.output_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        filename = self.output_listbox.get(idx)
        output_dir = os.path.join(os.getcwd(), "OllamaDataPrep", "output")
        full_path = os.path.join(output_dir, filename)
        meta_path = full_path + ".meta.json"

        if messagebox.askyesno("Confirm", f"Delete {filename}?"):
            if os.path.exists(full_path):
                os.remove(full_path)
            if os.path.exists(meta_path):
                os.remove(meta_path)
            self.refresh_output_list()
            self.metadata_text.configure(state="normal")
            self.metadata_text.delete("1.0", tk.END)
            self.metadata_text.configure(state="disabled")
            self.viewer_text.configure(state="normal")
            self.viewer_text.delete("1.0", tk.END)
            self.viewer_text.configure(state="disabled")

    def extract_instruction_pairs(self, file_path):
        records = []
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        for i in range(0, len(lines) - 1, 2):
            q = lines[i]
            a = lines[i+1]
            records.append({
                "instruction": q,
                "input": "",
                "output": a
            })
        return records

    def extract_plain_text(self, file_path):
        records = []
        with open(file_path, "r", encoding="utf-8") as f:
            paragraphs = [p.strip() for p in f.read().split("\n\n") if p.strip()]
        for para in paragraphs:
            records.append({
                "instruction": "Summarize the following text.",
                "input": para,
                "output": ""
            })
        return records

    def extract_squad_pairs(self, file_path):
        records = []
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        examples = data.get("data", [])
        for entry in examples:
            paragraphs = entry.get("paragraphs", [])
            for para in paragraphs:
                context = para.get("context", "")
                qas = para.get("qas", [])
                for qa in qas:
                    question = qa.get("question", "")
                    answers = qa.get("answers", [])
                    if answers:
                        answer_text = answers[0].get("text", "")
                    else:
                        answer_text = "CANNOTANSWER"
                    records.append({
                        "instruction": question,
                        "input": context,
                        "output": answer_text
                    })
        return records

if __name__ == "__main__":
    import ttkbootstrap as tb
    root = tb.Window(themename="darkly")
    app = OllamaDataPrep(root)
    root.mainloop()
