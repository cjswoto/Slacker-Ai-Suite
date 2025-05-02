import os
import subprocess
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SPEC_FILE = os.path.join(PROJECT_ROOT, "samples", "task_spec.json")

def load_spec():
    with open(SPEC_FILE, 'r') as f:
        return json.load(f)

def lint_files(project_name):
    success = True
    for root, _, files in os.walk(os.path.join(PROJECT_ROOT, project_name)):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    subprocess.check_output(["python", "-m", "py_compile", path])
                except subprocess.CalledProcessError:
                    success = False
    return success

def main():
    spec = load_spec()
    project_name = spec["project_name"]

    print("\n--- Phase 4 Test ---\n")

    if not lint_files(project_name):
        print("❌ Syntax errors found after evolution.")
        print("\n⚠️ Phase 4 Test: FAILED\n")
    else:
        print("✅ Evolved project syntax is valid.")
        print("\n🎯 Phase 4 Test: SUCCESS\n")

if __name__ == "__main__":
    main()
