import json
import os
import urllib.request

BASE_URL = os.environ.get("LMSTUDIO_URL", "http://localhost:1234/v1")


def _post(path, payload, timeout=120):
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def list_models():
    with urllib.request.urlopen(f"{BASE_URL}/models", timeout=10) as resp:
        return [m["id"] for m in json.loads(resp.read())["data"]]


def chat_json(model, system, user, schema, temperature=0.0):
    """Ask the model for an answer that must follow a JSON schema (structured output)."""
    payload = {
        "model": model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "disclosure", "strict": True, "schema": schema},
        },
    }
    out = _post("/chat/completions", payload)
    return json.loads(out["choices"][0]["message"]["content"])
