"""
code_generator.py

Coordinates the prompt building, model querying, and writes generated code
into the appropriate scaffolded project files.
"""

import os
import json
from codegen.prompt_builder import build_prompt
from codegen.model_connector import send_prompt
from codegen.spec_interpreter import SpecInterpreter

SPEC_FILE = "samples/task_spec.json"

def load_spec():
    with open(SPEC_FILE, 'r') as f:
        return json.load(f)

def generate_code():
    spec = load_spec()
    project_name = spec["project_name"]
    prompt_type = "mcp_service" if spec.get("mcp_compliance", False) else "generic_service"

    prompt = build_prompt(spec, prompt_type)
    generated_code = send_prompt(prompt)

    output_dir = os.path.join("output", project_name)
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "generated_code.txt")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(generated_code)

    print(f"✅ Generated code written to {output_file}")

if __name__ == "__main__":
    generate_code()
