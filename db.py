import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

env_file = Path(__file__).resolve().parent / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)
else:
    load_dotenv()

_url = os.getenv("SUPABASE_URL")
_key = os.getenv("SUPABASE_SERVICE_KEY")

if not _url or not _key:
    raise RuntimeError(
        "Missing database credentials! Please set SUPABASE_URL and SUPABASE_SERVICE_KEY "
        "in your .env file or environment variables."
    )

supabase: Client = create_client(_url, _key)
