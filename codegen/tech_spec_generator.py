# codegen/tech_spec_generator.py
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
OLLAMA_MODEL    = cfg.model_name

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

def build_tech_spec_prompt(user_description: str) -> str:
    """
    Build a prompt to generate a detailed MCP-compliant technical specification JSON.
    """
    return (
        "You are a system architect. Based on the user description, generate a detailed technical specification "
        "in valid JSON format following the MCP compliance schema. The schema includes:\n"
        "- components: list of modules with interfaces, classes, functions\n"
        "- data_models: data structures and types\n"
        "- workflows: step-by-step workflows\n"
        "- dependencies: list of required libraries\n"
        "- entry_point: should be 'main.py'\n"
        "Produce only raw JSON, no markdown or commentary.\n\n"
        f"User Description:\n{user_description}\n"
    )

def request_tech_spec(prompt: str) -> str:
    """
    Send the tech spec prompt to Ollama and return the raw JSON spec string.
    Retries on transient network failures.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": "You are an expert technical spec generator."},
            {"role": "user",   "content": prompt}
        ],
        "stream": False
    }
    data = _post(payload)
    # Ollama returns { "message": { "content": "..." } }
    if isinstance(data, dict) and "message" in data and "content" in data["message"]:
        return data["message"]["content"]
    return json.dumps(data)
