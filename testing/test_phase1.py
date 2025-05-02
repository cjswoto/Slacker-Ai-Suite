import os
import json
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SPEC_FILE = os.path.join(PROJECT_ROOT, "samples", "task_spec.json")

def load_spec():
    with open(SPEC_FILE, 'r') as f:
        return json.load(f)

def check_project_exists(project_name):
    return os.path.isdir(os.path.join(PROJECT_ROOT, project_name))

def check_files_exist(project_name, files):
    missing = []
    for file_entry in files:
        path = os.path.join(PROJECT_ROOT, project_name, file_entry["path"])
        if not os.path.isfile(path):
            missing.append(path)
    return missing

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
    files = spec["files"]

    passed = True
    print("\n--- Phase 1 Test ---\n")

    if not check_project_exists(project_name):
        print("❌ Project folder missing.")
        passed = False
    else:
        missing_files = check_files_exist(project_name, files)
        if missing_files:
            print(f"❌ Missing files: {missing_files}")
            passed = False
        else:
            print("✅ Project structure valid.")

    if not lint_files(project_name):
        print("❌ Syntax errors found.")
        passed = False
    else:
        print("✅ Syntax valid.")

    if passed:
        print("\n🎯 Phase 1 Test: SUCCESS\n")
    else:
        print("\n⚠️ Phase 1 Test: FAILED\n")

if __name__ == "__main__":
    main()
