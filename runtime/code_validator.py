"""
code_validator.py

Post-generation code validation routines.
Checks Python syntax after code is injected.
"""

import subprocess
import os

def validate_python_file(filepath: str) -> bool:
    try:
        subprocess.check_output(["python", "-m", "py_compile", filepath])
        print(f"✅ Syntax OK: {filepath}")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Syntax Error: {filepath}")
        return False

def validate_project(project_path: str) -> bool:
    success = True
    for root, _, files in os.walk(project_path):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                if not validate_python_file(full_path):
                    success = False
    return success
# Code Validator module placeholder.
