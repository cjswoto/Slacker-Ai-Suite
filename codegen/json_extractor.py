# codegen/json_extractor.py
import io
import json

try:
    import ijson
except ImportError:
    ijson = None

def extract_first_json(raw: str):
    """
    Extract the first top‐level JSON object from `raw`.
    Uses streaming via ijson if available; on any error, falls back
    to brute‐force substring scanning.
    """
    # Try streaming parse
    if ijson:
        stream = io.StringIO(raw)
        try:
            return next(ijson.items(stream, ""))
        except Exception:
            # e.g. IncompleteJSONError → fallback
            pass

    # Fallback: find first '{' and try loading progressively shorter slices
    start = raw.find("{")
    if start < 0:
        raise ValueError("No JSON object found in response")
    for end in range(len(raw), start, -1):
        snippet = raw[start:end]
        try:
            return json.loads(snippet)
        except json.JSONDecodeError:
            continue
    raise ValueError("Could not extract valid JSON from response")
