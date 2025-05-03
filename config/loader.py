import os
import yaml

class Config:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "config.yaml")

        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Top-level config values
        self.ollama_endpoint = data.get("ollama_endpoint", "http://localhost:11434")
        self.model_name = data.get("model_name", "codellama:latest")
        self.retry_count = data.get("retry_count", 3)
        self.retry_backoff_seconds = data.get("retry_backoff_seconds", 2)

        # Nested config values
        self.paths = data.get("paths", {})
        self.tech_schema = self.paths.get("tech_schema", "samples/schemas/tech_spec_schema.json")
        self.task_schema = self.paths.get("task_schema", "samples/schemas/task_spec_schema.json")
        self.tech_spec = self.paths.get("tech_spec", "samples/tech_spec.json")
        self.task_spec = self.paths.get("task_spec", "samples/task_spec.json")
        self.last_project_path = self.paths.get("last_project_path", "samples/last_project_path.txt")

        self.extra = data  # Optional catch-all

    def get(self, key, default=None):
        return self.extra.get(key, default)
