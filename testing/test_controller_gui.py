import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
import threading
import os

TESTS = {
    "Phase 1 Test": "test_phase1.py",
    "Phase 2 Test": "test_phase2.py",
    "Phase 3 Test": "test_phase3.py",
    "Phase 4 Test": "test_phase4.py"
}

class TestControllerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AISuite Test Controller")
        self.root.geometry("700x500")
        self.root.configure(bg="#1E1E2F")

        self.title_label = tk.Label(root, text="AISuite Test Controller", font=("Helvetica", 20, "bold"), bg="#1E1E2F", fg="white")
        self.title_label.pack(pady=20)

        self.button_frame = tk.Frame(root, bg="#1E1E2F")
        self.button_frame.pack(pady=10)

        for name, script in TESTS.items():
            tk.Button(self.button_frame, text=name, command=lambda s=script: self.run_test(s),
                      width=30, height=2, bg="#3A3A5D", fg="white", font=("Helvetica", 12)).pack(pady=5)

        tk.Button(self.button_frame, text="Run All Tests", command=self.run_all_tests,
                  width=30, height=2, bg="green", fg="white", font=("Helvetica", 12)).pack(pady=20)

        self.output_area = scrolledtext.ScrolledText(root, width=80, height=15, font=("Courier", 10), bg="#2D2D40", fg="white")
        self.output_area.pack(pady=10)

    def run_test(self, script_path):
        self.output_area.delete(1.0, tk.END)
        threading.Thread(target=self._execute_script, args=(script_path,)).start()

    def run_all_tests(self):
        self.output_area.delete(1.0, tk.END)
        threading.Thread(target=self._execute_all_scripts).start()

    def _execute_script(self, script_path):
        if not os.path.exists(script_path):
            self.output_area.insert(tk.END, f"❌ Script not found: {script_path}\n")
            return
        try:
            proc = subprocess.Popen(["python", script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = proc.communicate()

            if out:
                out = out.decode('utf-8', errors='replace')
                self.output_area.insert(tk.END, out)
            if err:
                err = err.decode('utf-8', errors='replace')
                self.output_area.insert(tk.END, err)
        except Exception as e:
            self.output_area.insert(tk.END, f"❌ Error running {script_path}: {e}\n")

    def _execute_all_scripts(self):
        for name, script in TESTS.items():
            self.output_area.insert(tk.END, f"\n--- Running {name} ---\n\n")
            self._execute_script(script)

def main():
    root = tk.Tk()
    app = TestControllerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
