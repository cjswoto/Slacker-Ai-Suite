import os

class ProjectPatcher:
    def __init__(self, project_path):
        self.project_path = project_path

    def split_refinement_output(self, generated_text):
        sections = {}
        current_file = None
        for line in generated_text.splitlines():
            if line.startswith("### FILE:"):
                current_file = line.replace("### FILE:", "").strip()
                sections[current_file] = ""
            elif current_file:
                sections[current_file] += line + "\n"
        return sections

    def apply_patches(self, sections):
        for rel_path, new_code in sections.items():
            full_path = os.path.join(self.project_path, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_code)
