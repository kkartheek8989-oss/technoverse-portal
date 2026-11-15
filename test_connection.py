"""
Technoverse Portal - Connection & System Verification Script
Run this script: python test_connection.py
"""

import os
import sys
from pathlib import Path

def run_checks():
    print("=" * 60)
    print(" Technoverse Portal: Pre-Flight Verification Check")
    print("=" * 60)

    # 1. Check .env file
    env_file = Path(__file__).resolve().parent / ".env"
    if not env_file.exists():
        print("❌ [FAIL] .env file not found!")
        print("   Please copy .env.example to .env and fill in your Supabase credentials.")
        return False
    print("✅ [PASS] .env file found.")

    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_file)

    secret_key = os.getenv("SECRET_KEY")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not secret_key or "generate" in secret_key:
        print("⚠️  [WARN] SECRET_KEY is not configured or using default placeholder.")
    else:
        print("✅ [PASS] SECRET_KEY is configured.")

    if not supabase_url or "your-project" in supabase_url:
        print("❌ [FAIL] SUPABASE_URL is not configured.")
        return False
    print(f"✅ [PASS] SUPABASE_URL: {supabase_url}")

    if not supabase_key or "your-secret-key" in supabase_key:
        print("❌ [FAIL] SUPABASE_SERVICE_KEY is not configured.")
        return False
    print("✅ [PASS] SUPABASE_SERVICE_KEY is configured.")

    # 2. Test Supabase Client Connection
    print("\nConnecting to Supabase...")
    try:
        from supabase import create_client
        client = create_client(supabase_url, supabase_key)
        print("✅ [PASS] Supabase client initialized.")
    except Exception as e:
        print(f"❌ [FAIL] Supabase connection error: {e}")
        return False

    # 3. Check Tables
    tables = [
        "members", "files", "tasks", "task_attachments", "events",
        "event_registrations", "attendance", "resources", "minutes",
        "action_items", "expenses", "sponsorships", "join_requests",
        "announcements", "notifications", "settings", "activity"
    ]

    missing = []
    print("\nVerifying database tables...")
    for t in tables:
        try:
            client.table(t).select("count", count="exact").limit(0).execute()
            print(f"  ✓ Table '{t}' exists.")
        except Exception:
            missing.append(t)
            print(f"  ✗ Table '{t}' NOT found.")

    if missing:
        print(f"\n❌ [FAIL] {len(missing)} tables missing: {', '.join(missing)}")
        print("   Please execute schema.sql in your Supabase SQL Editor!")
        return False
    else:
        print("\n✅ [PASS] All 17 tables are present in the database!")

    # 4. Check Storage Bucket
    print("\nVerifying Storage bucket 'club-files'...")
    try:
        buckets = client.storage.list_buckets()
        names = [b.name for b in buckets] if buckets else []
        if "club-files" in names:
            print("✅ [PASS] Storage bucket 'club-files' exists.")
        else:
            print("⚠️  [WARN] Bucket 'club-files' not listed yet. You can create it in Supabase Storage dashboard.")
    except Exception as e:
        print(f"⚠️  [NOTE] Storage check note: {e}")

    print("\n" + "=" * 60)
    print(" 🎉 ALL CORE CHECKS PASSED! The portal is ready to run.")
    print(" Run 'python app.py' to launch locally, or push to Vercel/Render.")
    print("=" * 60)
    return True

if __name__ == "__main__":
    run_checks()
