"""
spec_interpreter.py

Responsible for reading a task_spec.json file and creating the initial project structure.
Handles both generic and MCP-compliant service scaffolding.
"""

import os
import json

SPEC_REQUIRED_FIELDS = ["project_name", "description", "files"]

class SpecInterpreter:
    def __init__(self, spec_path: str):
        self.spec_path = spec_path
        self.spec_data = {}

    def load_spec(self):
        if not os.path.exists(self.spec_path):
            raise FileNotFoundError(f"Spec file not found: {self.spec_path}")

        with open(self.spec_path, 'r') as f:
            self.spec_data = json.load(f)

        for field in SPEC_REQUIRED_FIELDS:
            if field not in self.spec_data:
                raise ValueError(f"Missing required field in spec: {field}")

    def create_structure(self):
        project_name = self.spec_data["project_name"]
        if not os.path.exists(project_name):
            os.makedirs(project_name)

        for file_entry in self.spec_data.get("files", []):
            file_path = os.path.join(project_name, file_entry["path"])
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(f"# Purpose: {file_entry['purpose']}\n")

    def is_mcp_compliant(self) -> bool:
        return self.spec_data.get("mcp_compliance", False)

    def get_prompt_type(self) -> str:
        return "mcp_service" if self.is_mcp_compliant() else "generic_service"

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python spec_interpreter.py path/to/task_spec.json")
        exit(1)

    interpreter = SpecInterpreter(sys.argv[1])
    interpreter.load_spec()
    interpreter.create_structure()
    print(f"Project '{interpreter.spec_data['project_name']}' created successfully.")
