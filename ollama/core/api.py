import requests
import datetime

def get_models(ollama_url):
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [m["name"] for m in models]
        return []
    except Exception:
        return []

def check_server_connection(ollama_url):
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=3)
        return response.status_code == 200
    except Exception:
        return False

def generate_response(ollama_url, model, prompt, temperature=0.7, num_predict=2048):
    try:
        response = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": num_predict},
            },
        )
        if response.status_code == 200:
            ai_response = response.json().get("response", "")
            return {"success": True, "ai_response": ai_response}
        else:
            return {"success": False, "error": f"Server error: {response.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot connect to Ollama server. Is it running?"}
    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}"}
