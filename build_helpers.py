import os
import subprocess
import shutil

# 1. List all helper scripts you want to compile, relative to this script's folder.
#    Adjust these paths to match your actual folder structure inside OllamaFace3.
SCRIPTS = [
    "kb/kb_gui.py",
    "OllamaDataPrep/cuttrainfile.py",
    "OllamaDataPrep/ollamadataprep.py",
    "OllamaDataPrep/ollamatrainer.py",
    "OllamaDataPrep/PDFMaster.py",
    "ollama/api.py",
    "ollama/core_manager.py",
    "ollama/search.py",
    "ollama/session.py",
    "ollama/local_retriever.py"
    # Add more as needed
]

def remove_dir_if_exists(directory):
    """Delete a folder if it exists."""
    if os.path.exists(directory):
        print(f"Removing {directory} folder...")
        shutil.rmtree(directory)

def build_helpers():
    # 2. Optionally delete previous build artifacts
    remove_dir_if_exists("dist")
    remove_dir_if_exists("build")

    # 3. Compile each script in onedir mode
    for script_path in SCRIPTS:
        # Make sure the script file actually exists
        if not os.path.isfile(script_path):
            print(f"Skipping {script_path}: file not found.")
            continue

        print(f"Compiling {script_path}...")
        # --windowed creates a GUI app (no console). Remove if you need a console.
        result = subprocess.run(["pyinstaller", "--windowed", script_path])
        if result.returncode != 0:
            print(f"Error compiling {script_path}")
        else:
            print(f"Successfully compiled {script_path}")

    print("Done compiling helper scripts.")

if __name__ == "__main__":
    build_helpers()
    input("Press Enter to exit...")
