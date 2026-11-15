import os
from pathlib import Path
from dotenv import load_dotenv
import requests

env_file = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_file)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")

if not url or not key:
    print("Error: Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")
    exit(1)

endpoint = f"{url}/rest/v1/members?select=id&limit=1"
headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}"
}

try:
    resp = requests.get(endpoint, headers=headers, timeout=10)
    print(f"Supabase Status Code: {resp.status_code}")
    if resp.status_code in [200, 206]:
        print("✓ Supabase Keep-Alive Success: Database project is awake and active!")
    else:
        print(f"Response: {resp.text[:200]}")
except Exception as e:
    print("Heartbeat ping failed:", e)
