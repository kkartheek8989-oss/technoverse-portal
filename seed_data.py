"""
Technoverse Portal - Enterprise Database Seeder
Seeds core team leadership accounts and organization data into Supabase.
Run: python seed_data.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
import bcrypt

env_file = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_file)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")

if not url or not key:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
    exit(1)

client = create_client(url, key)

def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def seed():
    print("=" * 60)
    print(" Seeding Technoverse Club Organizational Data")
    print("=" * 60)

    # 1. Core Leadership Team
    team_members = [
        {"name": "Chandini.B", "roll": "COORD01", "email": "coordinator@technoverse.org", "role": "club_coordinator", "pw": "coordinator123", "branch": "CSE", "year": 4},
        {"name": "Aarav Sharma", "roll": "PRES01", "email": "president@technoverse.org", "role": "president", "pw": "president123", "branch": "CSE", "year": 4},
        {"name": "Ananya Iyer", "roll": "VP01", "email": "vp@technoverse.org", "role": "vice_president", "pw": "vicepres123", "branch": "IT", "year": 3},
        {"name": "Vikram Malhotra", "roll": "SEC01", "email": "secretary@technoverse.org", "role": "secretary", "pw": "secretary123", "branch": "ECE", "year": 3},
        {"name": "Rohan Varma", "roll": "TREAS01", "email": "treasurer@technoverse.org", "role": "treasurer", "pw": "treasurer123", "branch": "CSE", "year": 3},
        {"name": "Neha Reddy", "roll": "TECH01", "email": "techlead@technoverse.org", "role": "technical_lead", "pw": "techlead123", "branch": "AI & DS", "year": 3},
        {"name": "Aditya Nair", "roll": "EVENT01", "email": "events@technoverse.org", "role": "event_coordinator", "pw": "eventcoord123", "branch": "IT", "year": 2},
        {"name": "Pooja Krishnan", "roll": "MEM01", "email": "member@technoverse.org", "role": "member", "pw": "member123", "branch": "CSE", "year": 2}
    ]

    print("\n1. Provisioning Core Team Accounts...")
    created_members = {}
    for m in team_members:
        try:
            res = client.table("members").upsert({
                "name": m["name"],
                "roll": m["roll"],
                "email": m["email"],
                "role": m["role"],
                "pw_hash": hash_pw(m["pw"]),
                "branch": m["branch"],
                "year": m["year"],
                "active": True
            }, on_conflict="roll").execute()
            if res.data:
                created_members[m["role"]] = res.data[0]["id"]
                print(f"  ✓ Created/Updated: {m['role'].upper()} -> Roll: {m['roll']} | PW: {m['pw']}")
        except Exception as e:
            print(f"  ✗ Failed {m['roll']}: {e}")

    coord_id = created_members.get("club_coordinator")
    pres_id = created_members.get("president")
    tech_id = created_members.get("technical_lead")
    event_id = created_members.get("event_coordinator")
    sec_id = created_members.get("secretary")
    treas_id = created_members.get("treasurer")

    # 2. Flagship Events
    print("\n2. Scheduling Flagship Events...")
    events_data = [
        {"title": "CodeX 2026: 36-Hour National Hackathon", "category": "Hackathon", "flagship": "CodeX", "venue": "Main Innovation Labs & Auditorium", "quota": 250, "starts_at": "2026-12-05T09:00:00Z", "ends_at": "2026-12-06T21:00:00Z", "description": "Annual flagship hackathon featuring Web3, AI Agents, and Cloud Security tracks with ₹1,50,000 in cash prizes.", "created_by": event_id},
        {"title": "AI Nexus Summit: Generative AI & LLM Systems", "category": "Technical", "flagship": "AI Nexus", "venue": "Audi-2 (Seminar Hall)", "quota": 150, "starts_at": "2026-11-28T14:00:00Z", "ends_at": "2026-11-28T18:00:00Z", "description": "Hands-on engineering workshop on RAG pipelines, autonomous agents, and inference optimization.", "created_by": tech_id},
        {"title": "CyberShield CTF: Ethical Hacking Challenge", "category": "Workshop", "flagship": "CyberShield", "venue": "Network Security Lab 3", "quota": 80, "starts_at": "2026-12-12T10:00:00Z", "ends_at": "2026-12-12T17:00:00Z", "description": "Jeopardy-style Capture The Flag competition covering cryptography, reverse engineering, and web security.", "created_by": event_id}
    ]

    for ev in events_data:
        try:
            client.table("events").insert(ev).execute()
            print(f"  ✓ Scheduled Event: {ev['title']}")
        except Exception as e:
            print(f"  ✗ Event error: {e}")

    # 3. Tasks
    print("\n3. Populating Deliverables & Kanban Tasks...")
    tasks_data = [
        {"title": "Finalize CodeX 2026 Problem Statements", "description": "Collaborate with industry sponsors to draft tracks for AI, Web3, and Open Innovation.", "priority": "urgent", "status": "doing", "sprint": "Sprint 1", "assigned_to": tech_id, "created_by": pres_id},
        {"title": "Confirm Audi-2 Sound System & Microphones", "description": "Test AV mixer and presentation display before Friday's technical workshop.", "priority": "high", "status": "todo", "sprint": "Sprint 1", "assigned_to": event_id, "created_by": coord_id},
        {"title": "Publish Club Finance Ledger for Q3", "description": "Reconcile vendor invoices and upload PDF statement to files repository.", "priority": "medium", "status": "done", "sprint": "Sprint 1", "assigned_to": treas_id, "created_by": pres_id},
        {"title": "Review First Year Join Applications", "description": "Interview 15 shortlisted candidates for Web and Design sub-teams.", "priority": "high", "status": "doing", "sprint": "Sprint 1", "assigned_to": sec_id, "created_by": pres_id},
        {"title": "Deploy Technoverse Portal v2 to Vercel", "description": "Configure environment variables, Supabase connection, and custom domain SSL.", "priority": "urgent", "status": "done", "sprint": "Sprint 1", "assigned_to": coord_id, "created_by": coord_id}
    ]

    for t in tasks_data:
        try:
            client.table("tasks").insert(t).execute()
            print(f"  ✓ Added Task: {t['title']} [{t['status'].upper()}]")
        except Exception as e:
            print(f"  ✗ Task error: {e}")

    # 4. Learning Resources
    print("\n4. Publishing Technical Curricula...")
    learning_data = [
        {"title": "Full-Stack Web Engineering with FastHTML & Tailwind", "track": "Web Development", "level": "intermediate", "link_url": "https://fastht.ml/docs", "summary": "Comprehensive architectural guide to building hypermedia-driven web applications in pure Python.", "created_by": tech_id},
        {"title": "Production LLM Engineering & Agentic Workflows", "track": "AI & Machine Learning", "level": "advanced", "link_url": "https://github.com", "summary": "Hands-on guide to building multi-agent swarms, tool calling, and vector storage retrieval.", "created_by": tech_id},
        {"title": "Practical Web Application Penetration Testing", "track": "Cyber Security", "level": "beginner", "link_url": "https://owasp.org", "summary": "OWASP Top 10 vulnerabilities, burp suite workflows, and defensive secure coding practices.", "created_by": tech_id}
    ]

    for l in learning_data:
        try:
            client.table("resources").insert(l).execute()
            print(f"  ✓ Added Resource: {l['title']}")
        except Exception as e:
            print(f"  ✗ Resource error: {e}")

    # 5. Finance (Sponsorships & Expenses)
    print("\n5. Initializing Financial Ledger...")
    sponsors_data = [
        {"sponsor": "DevCloud Solutions India", "amount": 75000, "status": "received"},
        {"sponsor": "Nexus AI Labs", "amount": 50000, "status": "received"},
        {"sponsor": "Apex CyberSecurity Corp", "amount": 35000, "status": "pledged"}
    ]
    for s in sponsors_data:
        try:
            client.table("sponsorships").insert(s).execute()
            print(f"  ✓ Sponsorship: ₹{s['amount']:,} from {s['sponsor']}")
        except Exception as e:
            print(f"  ✗ Sponsor error: {e}")

    expenses_data = [
        {"description": "Refreshments & High-Tea for 150 AI Workshop Attendees", "amount": 6500, "status": "approved", "submitted_by": event_id, "approved_by": treas_id},
        {"description": "Branded Tech Club Lanyards & ID Badges (100 units)", "amount": 4200, "status": "approved", "submitted_by": sec_id, "approved_by": treas_id},
        {"description": "CodeX 2026 Winner Trophy Mementos & Certificates", "amount": 8500, "status": "pending", "submitted_by": event_id}
    ]
    for ex in expenses_data:
        try:
            client.table("expenses").insert(ex).execute()
            print(f"  ✓ Expense: ₹{ex['amount']:,} - {ex['description'][:30]}...")
        except Exception as e:
            print(f"  ✗ Expense error: {e}")

    # 6. Meeting Minutes
    print("\n6. Recording Meeting Minutes...")
    try:
        min_res = client.table("minutes").insert({
            "title": "Executive Planning Session #04: Semester Roadmap",
            "held_at": "2026-11-10T17:00:00Z",
            "summary": "Reviewed CodeX hackathon timeline, allocated ₹45,000 preliminary budget, approved recruitment drive, and assigned technical leads to curriculum drafting.",
            "created_by": sec_id
        }).execute()
        if min_res.data:
            mid = min_res.data[0]["id"]
            client.table("action_items").insert([
                {"minutes_id": mid, "text": "Draft formal sponsorship deck for corporate outreach"},
                {"minutes_id": mid, "text": "Reserve Audi-2 for November technical workshop"},
                {"minutes_id": mid, "text": "Update Technoverse Portal access roles"}
            ]).execute()
            print("  ✓ Saved Meeting Minutes #04 with 3 Action Items")
    except Exception as e:
        print(f"  ✗ Minutes error: {e}")

    # 7. Join Requests
    print("\n7. Ingesting Candidate Applications...")
    candidates = [
        {"name": "Siddharth Verma", "roll": "26ET106041", "branch": "CSE", "year": 1, "message": "Passionate about full-stack web and competitive programming. Looking to contribute to club projects.", "status": "pending"},
        {"name": "Riya Sen", "roll": "26ET106095", "branch": "AI & DS", "year": 1, "message": "Active member in campus AI clubs, experienced with PyTorch and open source.", "status": "pending"}
    ]
    for c in candidates:
        try:
            client.table("join_requests").insert(c).execute()
            print(f"  ✓ Candidate: {c['name']} ({c['branch']})")
        except Exception as e:
            print(f"  ✗ Join request error: {e}")

    # 8. Activity log
    print("\n8. Recording Initial Audit Rows...")
    try:
        client.table("activity").insert({
            "member_name": "Chandini.B",
            "role": "club_coordinator",
            "action": "system_bootstrap",
            "section": "auth",
            "summary": "Bootstrapped Technoverse Portal organizational governance system"
        }).execute()
        print("  ✓ Initialized audit log")
    except Exception as e:
        print(f"  ✗ Activity log error: {e}")

    print("\n" + "=" * 60)
    print(" 🎉 SEED COMPLETE! All organization data & accounts are live.")
    print("=" * 60)

if __name__ == "__main__":
    seed()
