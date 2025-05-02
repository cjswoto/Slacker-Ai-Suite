# codegen/spec_generator.py
# -*- coding: utf-8 -*-

import requests
import json
import logging
from config.loader import Config

# ——— Load your configured Ollama endpoint ——————————————————————————
cfg = Config()
endpoint = cfg.ollama_endpoint.rstrip("/")

# Strip off any accidental /api/chat or /api/generate suffixes to get the base URL
if endpoint.endswith("/api/chat"):
    base_url = endpoint[: -len("/api/chat")]
elif endpoint.endswith("/api/generate"):
    base_url = endpoint[: -len("/api/generate")]
else:
    base_url = endpoint

# ——— Logging setup ——————————————————————————————————————————
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


def list_available_models() -> list[str]:
    """
    Fetch the list of locally installed Ollama models via GET /api/tags.
    Returns a list of model names.
    """
    url = f"{base_url}/api/tags"
    logger.info(f"Listing models from {url}")
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        raw = data.get("models", [])
        names = [m.get("name") for m in raw if isinstance(m, dict) and "name" in m]
        logger.info(f"Models found: {names}")
        return names
    except Exception as e:
        logger.error(f"Failed to list models at {url}: {e!r}")
        return []


def send_prompt_for_spec(raw_tech: str, model_name: str) -> str:
    """
    Send the raw technical spec JSON to Ollama’s /api/chat endpoint to generate
    a task-spec. Instruct the model to output only JSON conforming to the
    TaskSpec schema (no markdown, code fences, or additional text).
    Returns the model’s JSON response as a string.
    """
    url = f"{base_url}/api/chat"
    logger.info(f"Requesting task spec generation at {url} (model={model_name})")

    # System-level instructions to ensure JSON-only output
    system_prompt = (
        "You are an expert task-spec generator. "
        "Given a technical specification in JSON, generate a task specification in valid JSON format. "
        "Do NOT include any markdown, code fences, or commentary—only raw JSON. "
        "The output must conform to the TaskSpec schema: project_name, description, and files."
    )
    user_prompt = f"TECHNICAL_SPEC_JSON:\n{raw_tech}"

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False
    }

    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    # Ollama returns { "message": { "content": "..." } }
    if isinstance(data, dict) and "message" in data and "content" in data["message"]:
        return data["message"]["content"]

    # Fallback: dump entire response
    logger.warning(f"Unexpected response shape: {data!r}")
    return json.dumps(data)
