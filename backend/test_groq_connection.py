"""
Quick standalone test: verifies your GROQ_API_KEY works before relying on
it inside the full DDR generation pipeline.

Usage (from the backend/ folder, with your venv activated):
    python test_groq_connection.py
"""

import os
import sys

# Load .env manually here so this script works even before the full app
# config is wired up.
def _load_dotenv(path=".env"):
    if not os.path.exists(path):
        print(f"ERROR: {path} not found. Create it in the backend/ folder first.")
        sys.exit(1)
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()

api_key = os.environ.get("GROQ_API_KEY", "")
model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

if not api_key:
    print("ERROR: GROQ_API_KEY is empty. Check your .env file.")
    sys.exit(1)

if not api_key.startswith("gsk_"):
    print(f"WARNING: key doesn't start with 'gsk_' - double check you copied it correctly.")

print(f"Found API key (starts with: {api_key[:7]}...)")
print(f"Testing model: {model}")
print("Sending test request to Groq...")

import httpx

try:
    response = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": [
                {"role": "user", "content": "Reply with exactly: Connection successful."}
            ],
            "max_tokens": 20,
        },
        timeout=15.0,
    )
    response.raise_for_status()
    data = response.json()
    reply = data["choices"][0]["message"]["content"]
    print()
    print("SUCCESS!")
    print(f"Model replied: {reply}")
except httpx.HTTPStatusError as e:
    print()
    print(f"FAILED: HTTP {e.response.status_code}")
    print(f"Response: {e.response.text}")
    if e.response.status_code == 401:
        print("This usually means the API key is invalid or wasn't copied correctly.")
except Exception as e:
    print()
    print(f"FAILED: {type(e).__name__}: {e}")
