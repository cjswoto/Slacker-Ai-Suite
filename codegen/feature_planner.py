import requests

OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
MODEL_NAME = "your-model-name-here"

def build_feature_planning_prompt(project_summary):
    prompt = (
        "You are a project evolution agent.\n"
        "Based on the following project code, propose a new feature or enhancement.\n"
        "Respond by generating a full updated task_spec.json structure ONLY.\n"
        "Here is the current project:\n\n"
        f"{project_summary}"
    )
    return prompt

def request_feature_plan(prompt):
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(OLLAMA_ENDPOINT, json=payload)
    response.raise_for_status()
    return response.json()["response"]
