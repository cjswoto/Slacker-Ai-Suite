"""
prompt_builder.py

Generates structured prompts for code generation based on the task_spec.json
and the appropriate template (generic or MCP), with GUI detection.
"""

import os

def load_template(prompt_type: str) -> str:
    path = os.path.join("codegen", "prompt_templates", f"{prompt_type}.txt")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def detect_gui_requirement(spec: dict) -> bool:
    gui_keywords = ["gui", "graphical interface", "window", "tkinter", "PyQt", "display screen"]
    description = spec.get("description", "").lower()

    if any(keyword in description for keyword in gui_keywords):
        return True

    for file in spec.get("files", []):
        purpose = file.get("purpose", "").lower()
        if any(keyword in purpose for keyword in gui_keywords):
            return True

    return False

def build_prompt(spec: dict, prompt_type: str) -> str:
    template = load_template(prompt_type)
    file_list = "\n".join(
        [f"- {file['path']}: {file['purpose']}" for file in spec["files"]]
    )
    special_notes = "This project requires a graphical user interface (GUI). Use tkinter for implementation." if detect_gui_requirement(spec) else "No GUI required."

    prompt = template.format(
        project_name=spec["project_name"],
        description=spec["description"],
        file_list=file_list,
        exposed_tools="\n".join(
            [f"- {tool['name']}: {tool['description']}" for tool in spec.get("exposed_tools", [])]
        ),
        exposed_resources="\n".join(
            [f"- {res['name']}: {res['description']}" for res in spec.get("exposed_resources", [])]
        ),
        exposed_prompts="\n".join(
            [f"- {pr['name']}: {pr['description']}" for pr in spec.get("exposed_prompts", [])]
        ),
        metadata=spec.get("metadata", {}),
        dependencies=", ".join(spec.get("dependencies", [])),
        special_notes=special_notes
    )
    return prompt
