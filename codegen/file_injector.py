"""
file_injector.py

Splits the generated code from the model
and injects code into the appropriate scaffolded files.
"""

import os

def split_code_into_files(generated_code: str) -> dict:
    sections = {}
    current_file = None
    for line in generated_code.splitlines():
        if line.startswith("### FILE:"):
            current_file = line.replace("### FILE:", "").strip()
            sections[current_file] = ""
        elif current_file:
            sections[current_file] += line + "\n"
    return sections

def write_code_sections(project_path: str, sections: dict):
    for filename, content in sections.items():
        file_path = os.path.join(project_path, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
