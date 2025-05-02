# codegen/refiner.py
# -*- coding: utf-8 -*-
import requests
import json
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from config.loader import Config

cfg = Config()

OLLAMA_CHAT_URL = cfg.ollama_endpoint
MODEL_NAME      = cfg.model_name

@retry(
    stop=stop_after_attempt(cfg.retry_count),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(requests.RequestException),
    reraise=True
)
def _post(payload: dict) -> dict:
    resp = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()

def build_refinement_prompt(project_summary: str) -> str:
    """
    Build a code-refinement prompt given the full project code summary.
    """
    return (
        "BEST PRACTICE: main.py is always the entry point. It should import your modules and\n"
        "define:\n"
        "    def main():\n"
        "        ...\n"
        "    if __name__ == '__main__':\n"
        "        main()\n\n"
        "You are a code quality and style expert. You will only output valid, PEP8-compliant Python code.\n"
        "Do NOT include any Markdown fences (```) or bullet lists—only raw .py content.\n"
        "Indent with 4 spaces, keep lines under 88 characters, close all quotes and parentheses.\n"
        "Ensure the final code:\n"
        "  • Uses Python 3 type hints on all function signatures.\n"
        "  • Includes Google-style docstrings on every class and method.\n"
        "  • Catches division by zero via ZeroDivisionError -> ValueError.\n"
        "  • Uses snake_case for variables and methods.\n"
        "Analyze the following project code and suggest improvements for style, functionality, and structure.\n"
        "Respond by providing full, corrected code blocks for each file in this exact format:\n"
        "### FILE: <relative_path>\n"
        "<complete corrected code>\n\n"
        f"Here is the project code to refine:\n\n{project_summary}"
    )

def request_refinement(prompt: str) -> str:
    """
    Send the given refinement prompt to the Ollama chat endpoint and return the assistant's reply.
    Retries on transient network failures.
    """
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system",  "content": "You are a code quality and style assistant."},
            {"role": "user",    "content": prompt}
        ],
        "stream": False
    }
    data = _post(payload)
    if isinstance(data, dict) and "message" in data and isinstance(data["message"], dict):
        return data["message"].get("content", "")
    return json.dumps(data)
