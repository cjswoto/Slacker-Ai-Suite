import os

class SelfAnalyzer:
    def __init__(self, project_path):
        self.project_path = project_path

    def collect_source_files(self):
        files = []
        for root, _, filenames in os.walk(self.project_path):
            for filename in filenames:
                if filename.endswith(".py"):
                    files.append(os.path.join(root, filename))
        return files

    def create_summary(self):
        summaries = []
        files = self.collect_source_files()
        for file in files:
            with open(file, 'r', encoding='utf-8') as f:
                code = f.read()
                summaries.append(f"### FILE: {file}\n{code}\n")
        return "\n".join(summaries)
