import json
from datetime import datetime, timezone
from db import supabase

# Verified university defaults
DEFAULT_CONFIG = {
    # Identity & University Affiliation
    "site_title": "Technoverse",
    "university_name": "Hari University",
    "university_status": "Deemed to be University",
    "site_tagline": "Code • Innovate • Secure • Transform",
    "hero_headline": "Empowering Next-Generation Engineers",
    "hero_subtext": "Empowering next-generation engineers, researchers, and builders at Hari University through high-impact technical development, competitive hackathons, and enterprise-grade engineering tracks.",
    "footer_text": "Built by Technoverse. All rights reserved.",
    
    # Core Pillars
    "pillar1_title": "Software & Systems",
    "pillar1_desc": "Building scalable full-stack applications, open-source utilities, and developer tooling.",
    "pillar2_title": "AI & Machine Learning",
    "pillar2_desc": "Autonomous agentic swarms, fine-tuned neural models, and enterprise RAG pipelines.",
    "pillar3_title": "Cyber Defense & CTF",
    "pillar3_desc": "Offensive security research, ethical penetration testing, and national security challenges.",
    "pillar4_title": "Cloud & Infrastructure",
    "pillar4_desc": "Microservices, containerization, distributed databases, and high-availability operations.",

    # Global Announcement & Ticker
    "announcement_ticker": "🚀 CodeX 2026 National Hackathon registrations are officially open! Check the Events tab for tracks and prizes.",
    "alert_banner_enabled": "false",
    "alert_banner_text": "Executive Notice: Committee meeting scheduled this Friday at 4:30 PM in Seminar Hall 204.",
    "alert_banner_type": "amber",  # amber, primary, red, emerald

    # Club Operating Parameters
    "contact_email": "technoverse@hari.edu.in",
    "meeting_schedule": "Every Wednesday 4:30 PM at Lab 4",
    "recruitment_status": "Open for Core Team Nominations",
    "maintenance_mode": "false",
    "maintenance_message": "Technoverse Portal is undergoing scheduled university maintenance. Please check back shortly."
}

_cache = None
_cache_time = 0

def get_site_config(force_reload: bool = False) -> dict:
    global _cache, _cache_time
    import time
    now = time.time()
    if _cache and not force_reload and (now - _cache_time) < 60:
        return _cache

    config = dict(DEFAULT_CONFIG)
    try:
        rows = supabase.table("settings").select("key, value").execute().data or []
        for r in rows:
            k = r.get("key")
            v = r.get("value")
            if k in config and v is not None:
                config[k] = v
    except Exception as e:
        print("Warning: could not fetch settings from db, using defaults:", e)

    _cache = config
    _cache_time = now
    return config

def update_site_setting(key: str, value: str) -> bool:
    global _cache
    clean_val = str(value if value is not None else "").strip()
    try:
        supabase.table("settings").upsert({"key": key, "value": clean_val}).execute()
        if _cache:
            _cache[key] = clean_val
        return True
    except Exception as e:
        print(f"Error updating setting {key}:", e)
        return False

def bulk_update_settings(settings_dict: dict) -> bool:
    global _cache
    rows = [{"key": k, "value": str(v if v is not None else "").strip()} for k, v in settings_dict.items()]
    try:
        supabase.table("settings").upsert(rows).execute()
        if _cache:
            _cache.update(settings_dict)
        else:
            get_site_config(force_reload=True)
        return True
    except Exception as e:
        print("Error bulk updating settings:", e)
        return False

def reset_settings_to_defaults() -> bool:
    global _cache
    try:
        rows = [{"key": k, "value": v} for k, v in DEFAULT_CONFIG.items()]
        supabase.table("settings").upsert(rows).execute()
        _cache = dict(DEFAULT_CONFIG)
        return True
    except Exception as e:
        print("Error resetting settings to defaults:", e)
        return False
