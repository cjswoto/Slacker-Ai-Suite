import os

class ProjectAnalyzer:
    def __init__(self, project_path):
        self.project_path = project_path

    def collect_source_files(self):
        files = []
        for root, _, filenames in os.walk(self.project_path):
            for filename in filenames:
                if filename.endswith(".py"):
                    full_path = os.path.join(root, filename)
                    files.append(full_path)
        return files

    def summarize_project(self):
        files = self.collect_source_files()
        summaries = []
        for file_path in files:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
                summaries.append(f"### FILE: {file_path}\n{code}\n")
        return "\n".join(summaries)
