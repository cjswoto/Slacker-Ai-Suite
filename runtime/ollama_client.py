"""
ollama_client.py

Abstraction layer over direct Ollama API calls
for sending prompts and receiving generated responses.
"""

import requests

OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"

class OllamaClient:
    def __init__(self, model_name: str):
        self.model_name = model_name

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }
        response = requests.post(OLLAMA_ENDPOINT, json=payload)
        response.raise_for_status()
        return response.json()["response"]
