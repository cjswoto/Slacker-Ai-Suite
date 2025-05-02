import json
from jsonschema import Draft7Validator

def load_json(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate(path_spec: str, path_schema: str):
    """
    Validates the JSON at `path_spec` against the JSON Schema at `path_schema`.
    Raises ValueError with detailed messages on any violations.
    """
    spec   = load_json(path_spec)
    schema = load_json(path_schema)

    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(spec), key=lambda e: e.path)
    if errors:
        msgs = []
        for e in errors:
            loc = ".".join(str(x) for x in e.path) or "<root>"
            msgs.append(f"{loc}: {e.message}")
        joined = "\n  ".join(msgs)
        raise ValueError(f"Schema validation failed for {path_spec}:\n  {joined}")
    return True
