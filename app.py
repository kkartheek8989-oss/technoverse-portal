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
            # Top Right: Official Hari University Logo & Seal
            Div(
                Img(src="/hari-university-logo.png", alt="Hari University Logo", cls="w-10 h-10 object-contain shrink-0 drop-shadow-md"),
                Div(
                    Span("Hari University", cls="font-heading font-bold text-xs text-white block leading-tight"),
                    Span("Deemed to be University", cls="text-[9px] text-amber font-mono font-medium block leading-tight"),
                    cls="text-left hidden sm:block"
                ),
                cls="fixed top-4 right-4 z-40 flex items-center gap-2.5 bg-white/5 border border-white/10 px-3 py-1.5 rounded-xl backdrop-blur shadow-lg"
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
            P(
                "Account creation is restricted to the Club Coordinator & President.",
                cls="text-xs text-muted text-center mt-6 pt-4 border-t border-white/5 font-mono"
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
    log_activity(session, "login", "auth", None, f"User {user.get('name')} logged in ({user.get('role')})")
    return go("/")

# Registration is restricted to Club Coordinator and President (via Team management)
@rt("/register", methods=["GET", "POST"])
def register_blocked(session):
    return go("/login?error=Direct+registration+is+restricted.+Only+the+Club+Coordinator+and+President+can+provision+new+accounts.")

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
import routes.president
import routes.vice_president
import routes.admin_control
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
    port = int(os.getenv("PORT", 5001))
    host = os.getenv("HOST", "0.0.0.0")
    serve(host=host, port=port)
