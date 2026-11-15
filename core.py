import os
from pathlib import Path
from fasthtml.common import *
from db import supabase
from theme import hdrs

BASE_DIR = Path(__file__).resolve().parent
STATIC_PATH = str(BASE_DIR / "public")

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set. Please set SECRET_KEY in your .env file or environment variables.")

app, rt = fast_app(
    secret_key=SECRET_KEY,
    hdrs=hdrs,
    pico=False,
    static_path=STATIC_PATH,
    max_age=30 * 24 * 3600
)

def current_user(session):
    uid = session.get("uid")
    if not uid:
        return None
    try:
        rows = supabase.table("members").select("*").eq("id", uid).eq("active", True).limit(1).execute().data
        return rows[0] if rows else None
    except Exception as e:
        print("Error fetching current user:", e)
        return None

def go(path):
    return RedirectResponse(path, status_code=303)
