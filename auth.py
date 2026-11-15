import bcrypt
from db import supabase

RANKS = {
    "member": 1,
    "secretary": 3,
    "treasurer": 3,
    "technical_lead": 3,
    "event_coordinator": 3,
    "vice_president": 4,
    "president": 4,
    "club_coordinator": 5
}

SECTION_OWNERS = {
    "minutes": "secretary",
    "finance": "treasurer",
    "learning": "technical_lead",
    "events": "event_coordinator"
}

def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def check_pw(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode(), hashed.encode())
    except (ValueError, TypeError, AttributeError):
        return False

def _first(res):
    return res.data[0] if (res and res.data) else None

def get_member_by_roll(roll: str):
    clean_roll = (roll or "").strip().upper()
    if not clean_roll:
        return None
    try:
        return _first(supabase.table("members").select("*").eq("roll", clean_roll).eq("active", True).limit(1).execute())
    except Exception as e:
        print("Error fetching member by roll:", e)
        return None

def get_member(member_id: str):
    if not member_id:
        return None
    try:
        return _first(supabase.table("members").select("*").eq("id", str(member_id)).limit(1).execute())
    except Exception as e:
        print("Error fetching member by id:", e)
        return None

def can(role: str, section: str, action: str = "view") -> bool:
    rank = RANKS.get(role, 1)
    if rank >= 4 or SECTION_OWNERS.get(section) == role:
        return True
    return action in ("read", "view")

def is_rank_4_plus(role: str) -> bool:
    return RANKS.get(role, 1) >= 4

def is_club_coordinator(role: str) -> bool:
    return role == "club_coordinator"

def log_activity(session, action, section, record_id=None, summary="", old_value=None, new_value=None):
    """Append-only audit row. Always records the REAL user, even during view-as."""
    if not session.get("uid"):
        return
    try:
        supabase.table("activity").insert({
            "member_id": session["uid"],
            "member_name": session.get("name"),
            "role": session.get("role"),
            "action": action,
            "section": section,
            "record_id": str(record_id) if record_id else None,
            "summary": summary,
            "old_value": old_value,
            "new_value": new_value
        }).execute()
    except Exception as e:
        print("activity log failed:", e)
