# config/loader.py
import os
import yaml

class Config:
    """
    Loads and exposes configuration from config/config.yaml.
    Access keys as attributes, e.g. cfg.ollama_endpoint or cfg.get_path('tech_spec').
    """
    def __init__(self, path: str = "config/config.yaml"):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            self._cfg = yaml.safe_load(f)

    def __getattr__(self, name: str):
        if name in self._cfg:
            return self._cfg[name]
        raise AttributeError(f"No config attribute '{name}'")

    def get_path(self, key: str) -> str:
        """
        Returns one of the named paths under the `paths:` section.
        E.g. cfg.get_path('tech_spec') -> "samples/tech_spec.json"
        """
        paths = self._cfg.get("paths", {})
        if key not in paths:
            raise KeyError(f"No path entry for '{key}' in config.paths")
        return paths[key]
