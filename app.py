import os
from datetime import datetime, timezone
from fasthtml.common import *
from core import app, rt, current_user, go, supabase
from components import *
from auth import hash_pw, check_pw, get_member_by_roll, log_activity

def auth_shell(*c):
    return (
        Title("Technoverse Portal"),
        Div(
            Div(
                Div(Img(src="/logo-full.png", alt="Technoverse Club logo", cls="w-72 mx-auto"), cls="bg-white rounded-2xl p-3 mb-6"),
                *c,
                cls="w-full max-w-sm"
            ),
            cls="min-h-screen flex items-center justify-center p-4"
        )
    )

def login_form(error="", roll=""):
    return auth_shell(
        card(
            Div(error, cls="bg-red-900/30 border border-red-500/30 p-3 rounded-lg text-red-200 text-sm mb-4") if error else "",
            H2("Welcome back", cls="font-heading font-bold text-xl mb-1"),
            P("Sign in with your roll number", cls="text-sm text-muted mb-6"),
            Form(
                input_field("Roll number", "roll", value=roll, placeholder="e.g. 26ET103047"),
                Div(
                    Label("Password", cls="block text-xs font-mono text-muted mb-1"),
                    Input(name="password", id="pw", type="password", required=True, cls="input w-full"),
                    Button(icon("visibility"), type="button", onclick="var p=document.getElementById('pw');p.type=p.type=='password'?'text':'password'", cls="text-muted text-xs mt-1"),
                    cls="mb-4"
                ),
                btn_primary("Sign in", type="submit", cls="w-full"),
                method="post",
                action="/login"
            ),
            P(A("First time? Create the first Club Coordinator account →", href="/setup", cls="text-primary hover:underline text-xs"), cls="text-center mt-4") if _no_members() else P("No account? Ask your Club Coordinator.", cls="text-sm text-muted text-center mt-4")
        )
    )

@rt("/login", methods=["GET"])
def login_get(session):
    if _no_members():
        return go("/setup")
    return go("/") if current_user(session) else login_form()

@rt("/login", methods=["POST"])
def login_post(session, roll: str, password: str):
    user = get_member_by_roll(roll)
    if not user or not check_pw(password, user.get("pw_hash", "")):
        return login_form("Invalid roll number or password.", roll)
    session.clear()
    session.update(uid=user["id"], name=user["name"], role=user["role"])
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        supabase.table("members").update({"last_login": now_iso}).eq("id", user["id"]).execute()
    except Exception as e:
        print("Warning: Failed to update last_login timestamp:", e)
    log_activity(session, "login", "auth", None, "User logged in")
    return go("/")

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
                input_field("Email", "email", type="email", placeholder="you@example.com"),
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
        return go("/login")  # setup works only once
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
