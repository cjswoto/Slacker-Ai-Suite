import requests

OLLAMA_BASE_URL = "http://localhost:11434"

def send_prompt(prompt_text, model_name="codellama:latest"):
    full_prompt = (
        "You are a code refinement AI.\n\n"
        "Take the following starter project code and improve it:\n\n"
        f"{prompt_text}"
    )

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a senior software engineer. Your task is to enhance and refine given project code."},
            {"role": "user", "content": full_prompt}
        ],
        "stream": False
    }

    response = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
    response.raise_for_status()

    result = response.json()

    if "message" in result and "content" in result["message"]:
        return result["message"]["content"]
    else:
        raise ValueError("Invalid response format from model.")
