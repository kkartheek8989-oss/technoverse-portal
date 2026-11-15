import os
from datetime import datetime, timezone
from fasthtml.common import *
from core import app, rt, current_user, go, supabase
from components import *
from auth import hash_pw, check_pw, get_member_by_roll, log_activity

def auth_shell(*c):
    return (
        Title("Technoverse Portal | Hari University"),
        Div(
            # Top Right: Hari University Logo & Crest
            Div(
                Img(src="/hari-university-logo.svg", alt="Hari University Logo", cls="w-9 h-9 rounded-full border border-white/20 bg-[#0b1f5c] p-0.5 shadow-md shrink-0"),
                Div(
                    Span("Hari University", cls="font-heading font-bold text-xs text-white block leading-tight"),
                    Span("Official Campus Portal", cls="text-[9px] text-amber font-mono font-medium block leading-tight"),
                    cls="text-left hidden sm:block"
                ),
                cls="fixed top-4 right-4 z-40 flex items-center gap-2 bg-white/5 border border-white/10 px-3 py-1.5 rounded-xl backdrop-blur shadow-lg"
            ),
            # Main Auth Content Card
            Div(
                Div(
                    Img(src="/logo-full.png", alt="Technoverse Club logo", cls="w-72 mx-auto"),
                    cls="bg-white rounded-2xl p-3 mb-6 shadow-xl"
                ),
                *c,
                P("Built by Technoverse. All rights reserved.", cls="text-xs font-mono text-muted text-center mt-6 pt-4 border-t border-white/5"),
                cls="w-full max-w-md my-8"
            ),
            cls="min-h-screen flex items-center justify-center p-4 relative bg-[#070d24]"
        )
    )

def login_form(error="", success="", roll=""):
    return auth_shell(
        card(
            Div(error, cls="bg-red-900/40 border border-red-500/30 p-3 rounded-xl text-red-200 text-sm mb-4") if error else "",
            Div(success, cls="bg-emerald-900/40 border border-emerald-500/30 p-3 rounded-xl text-emerald-200 text-sm mb-4") if success else "",
            H2("Welcome back", cls="font-heading font-bold text-2xl mb-1"),
            P("Sign in with your Hari University roll number", cls="text-sm text-muted mb-6"),
            Form(
                input_field("Roll Number", "roll", value=roll, placeholder="e.g. 26ET103047 or COORD01"),
                Div(
                    Label("Password", cls="block text-xs font-mono text-muted mb-1"),
                    Input(name="password", id="pw", type="password", required=True, cls="input w-full"),
                    Button(icon("visibility"), type="button", onclick="var p=document.getElementById('pw');p.type=p.type=='password'?'text':'password'", cls="text-muted text-xs mt-1 hover:text-white bg-transparent border-0 cursor-pointer"),
                    cls="mb-4"
                ),
                btn_primary("Sign in", type="submit", cls="w-full py-2.5 font-semibold text-base"),
                method="post",
                action="/login"
            ),
            Div(
                P("Don't have an account?", cls="text-xs text-muted"),
                A("Create an Account / Sign Up →", href="/register", cls="text-xs font-bold text-primary hover:underline ml-1"),
                cls="flex items-center justify-center mt-6 pt-4 border-t border-white/5"
            )
        )
    )

@rt("/login", methods=["GET"])
def login_get(session, error: str = "", success: str = ""):
    if current_user(session):
        return go("/")
    return login_form(error=error, success=success)

@rt("/login", methods=["POST"])
def login_post(session, roll: str, password: str):
    user = get_member_by_roll(roll)
    if not user or not check_pw(password, user.get("pw_hash", "")):
        return login_form(error="Invalid roll number or password.", roll=roll)
    session.clear()
    session.update(uid=user["id"], name=user["name"], role=user["role"])
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        supabase.table("members").update({"last_login": now_iso}).eq("id", user["id"]).execute()
    except Exception as e:
        print("Warning: Failed to update last_login timestamp:", e)
    log_activity(session, "login", "auth", None, "User logged in")
    return go("/")

@rt("/register", methods=["GET"])
def register_get(session, error: str = ""):
    if current_user(session):
        return go("/")
    return auth_shell(
        card(
            Div(error, cls="bg-red-900/40 border border-red-500/30 p-3 rounded-xl text-red-200 text-sm mb-4") if error else "",
            H2("Create Account", cls="font-heading font-bold text-2xl mb-1"),
            P("Join Technoverse Club at Hari University", cls="text-sm text-muted mb-6"),
            Form(
                input_field("Full Name", "name", placeholder="e.g. Rahul Sharma", required=True),
                Div(
                    input_field("Roll Number", "roll", placeholder="e.g. 26ET104088", required=True),
                    input_field("Email Address", "email", type="email", placeholder="rahul@hari.edu.in", required=True),
                    cls="grid grid-cols-1 sm:grid-cols-2 gap-3"
                ),
                Div(
                    select_field("Branch / Department", "branch", [
                        ("CSE", "Computer Science (CSE)"),
                        ("IT", "Information Tech (IT)"),
                        ("AI & DS", "AI & Data Science"),
                        ("Cyber Security", "Cyber Security"),
                        ("ECE", "Electronics & Comm (ECE)"),
                        ("General", "Other / General")
                    ]),
                    select_field("Year of Study", "year", [
                        ("1", "1st Year"),
                        ("2", "2nd Year"),
                        ("3", "3rd Year"),
                        ("4", "4th Year")
                    ]),
                    cls="grid grid-cols-1 sm:grid-cols-2 gap-3"
                ),
                Div(
                    input_field("Password (min 8 chars)", "pw", type="password", required=True),
                    input_field("Confirm Password", "confirm_pw", type="password", required=True),
                    cls="grid grid-cols-1 sm:grid-cols-2 gap-3"
                ),
                btn_primary("Create Member Account", type="submit", cls="w-full py-2.5 font-semibold text-base mt-2"),
                method="post",
                action="/register"
            ),
            Div(
                P("Already have an account?", cls="text-xs text-muted"),
                A("Sign in here →", href="/login", cls="text-xs font-bold text-primary hover:underline ml-1"),
                cls="flex items-center justify-center mt-6 pt-4 border-t border-white/5"
            )
        )
    )

@rt("/register", methods=["POST"])
def register_post(name: str, roll: str, email: str, pw: str, confirm_pw: str, branch: str = "CSE", year: int = 1):
    clean_roll = roll.strip().upper()
    clean_email = email.strip().lower()

    if len(pw) < 8:
        return register_get(None, error="Password must be at least 8 characters long.")
    if pw != confirm_pw:
        return register_get(None, error="Passwords do not match. Please verify and retry.")

    # Check for existing roll or email
    try:
        existing = supabase.table("members").select("id").or_(f"roll.eq.{clean_roll},email.eq.{clean_email}").limit(1).execute().data
        if existing:
            return register_get(None, error=f"An account with roll '{clean_roll}' or email already exists. Please log in.")
    except Exception as e:
        print("Duplicate check error:", e)

    # Insert new member account
    try:
        res = supabase.table("members").insert({
            "name": name.strip(),
            "roll": clean_roll,
            "email": clean_email,
            "role": "member",
            "branch": branch,
            "year": int(year or 1),
            "pw_hash": hash_pw(pw),
            "active": True
        }).execute()
        
        # Log to activity
        if res.data:
            new_uid = res.data[0]["id"]
            supabase.table("activity").insert({
                "member_id": new_uid,
                "member_name": name.strip(),
                "role": "member",
                "action": "account_created",
                "section": "auth",
                "summary": f"New member account registered: {name.strip()} ({clean_roll})"
            }).execute()

        return go("/login?success=Account+created+successfully!+Please+sign+in+with+your+credentials.")
    except Exception as e:
        print("Registration error:", e)
        return register_get(None, error=f"Registration failed: {str(e)[:150]}")

@rt("/logout", methods=["GET", "POST"])
def logout(session):
    log_activity(session, "logout", "auth", None, "User logged out")
    session.clear()
    return go("/login")

def _no_members():
    try:
        res = supabase.table("members").select("id", count="exact").limit(1).execute()
        return (res.count or 0) == 0
    except Exception as e:
        print("Warning: members query failed:", e)
        return False

@rt("/setup", methods=["GET"])
def setup_get(error: str = ""):
    try:
        if not _no_members():
            return go("/login")
    except Exception:
        pass
    return auth_shell(
        card(
            H2("Create first Club Coordinator", cls="font-heading font-bold text-xl mb-4"),
            Div(error, cls="text-red-300 text-sm mb-3") if error else "",
            Form(
                input_field("Name", "name", placeholder="e.g. Krishna Kartheek"),
                input_field("Roll number", "roll", placeholder="e.g. 26ET103047"),
                input_field("Email", "email", type="email", placeholder="you@hari.edu.in"),
                input_field("Password (min 8 characters)", "pw", type="password"),
                btn_primary("Create Account", type="submit", cls="w-full"),
                method="post",
                action="/setup"
            )
        )
    )

@rt("/setup", methods=["POST"])
def setup_post(name: str, roll: str, email: str, pw: str):
    if not _no_members():
        return go("/login")
    if len(pw) < 8:
        return go("/setup?error=Password+must+be+at+least+8+characters")
    supabase.table("members").insert({
        "name": name.strip(),
        "roll": roll.strip().upper(),
        "email": email.strip().lower(),
        "role": "club_coordinator",
        "pw_hash": hash_pw(pw)
    }).execute()
    return go("/login")

@rt("/health", methods=["GET"])
def health():
    try:
        supabase.table("members").select("id").limit(1).execute()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "db_error", "detail": str(e)[:200]}

# Register all application routes
import routes.dashboard
import routes.tasks
import routes.events
import routes.team
import routes.finance
import routes.minutes
import routes.learning
import routes.files
import routes.join
import routes.activity
import routes.settings

if __name__ == "__main__":
    serve()
