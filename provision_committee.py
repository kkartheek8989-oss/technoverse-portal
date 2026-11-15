import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
import bcrypt

env_file = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_file)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")

client = create_client(url, key)

def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

committee = [
    {"name": "Karthik", "roll": "26ET103047", "branch": "CSE-1", "role": "president", "mobile": "9032936677", "year": 3},
    {"name": "D. Yakshagna", "roll": "26ET104152", "branch": "CSM-3", "role": "vice_president", "mobile": "9894474159", "year": 3},
    {"name": "B. Sariyu", "roll": "26ET102005", "branch": "CSD", "role": "secretary", "mobile": "8519802425", "year": 3},
    {"name": "Chaitanya", "roll": "26ET104048", "branch": "CSM-1", "role": "treasurer", "mobile": "8639638181", "year": 3},
    {"name": "Harsha", "roll": "26ET1030", "branch": "CSE-1", "role": "technical_lead", "mobile": "7382620603", "year": 3},
    {"name": "Manikanta", "roll": "26ET103101", "branch": "CSE-2", "role": "technical_lead", "mobile": "9948856065", "year": 3},
    {"name": "Swetha", "roll": "26ET104126", "branch": "CSM-2", "role": "event_coordinator", "mobile": "7816013446", "year": 2},
    {"name": "B. Thanusree", "roll": "26ET101037", "branch": "CSC", "role": "event_coordinator", "mobile": "9281289762", "year": 2},
    {"name": "Sahasra", "roll": "26ET103065", "branch": "CSE-2", "role": "event_coordinator", "mobile": "9505499928", "year": 2},
]

print("Provisioning official committee members from image...")
for m in committee:
    pw = m["mobile"]
    email = f"{m['roll'].lower()}@hari.edu.in"
    res = client.table("members").upsert({
        "name": m["name"],
        "roll": m["roll"],
        "email": email,
        "branch": m["branch"],
        "role": m["role"],
        "pw_hash": hash_pw(pw),
        "year": m["year"],
        "active": True
    }, on_conflict="roll").execute()
    print(f"✓ Provisioned {m['name']:<15} | Roll: {m['roll']:<12} | Role: {m['role']:<18} | PW: {pw}")

# Ensure Chandini.B account exists
client.table("members").upsert({
    "name": "Chandini.B",
    "roll": "COORD01",
    "email": "coordinator@hari.edu.in",
    "branch": "CSE",
    "role": "club_coordinator",
    "pw_hash": hash_pw("coordinator123"),
    "year": 4,
    "active": True
}, on_conflict="roll").execute()
print("✓ Verified Chandini.B (COORD01 / coordinator123)")
