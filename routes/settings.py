from fasthtml.common import *
from core import rt, current_user, go, supabase
from components import *
from auth import RANKS, hash_pw, check_pw, log_activity
from cache import invalidate_cache

@rt("/settings", methods=["GET"])
def settings_get(session, tab: str = "profile", success: str = "", error: str = ""):
    u = current_user(session)
    if not u:
        return go("/login")
    role = session.get("view_as") or u["role"]
    rank = RANKS.get(role, 1)

    is_coordinator = (u["role"] in ("club_coordinator", "president"))

    header = Div(
        H1("Portal Settings & Governance", cls="font-heading font-bold text-2xl"),
        P("Manage your user security, account preferences, and organizational configuration", cls="text-sm text-secondary mt-1"),
        cls="mb-6"
    )

    tabs_nav = Div(
        A("Profile", href="/settings?tab=profile", cls=f"px-4 py-2 font-mono text-xs font-semibold rounded-lg {'bg-primary text-white' if tab == 'profile' else 'text-muted hover:bg-white/5'}"),
        A("Security & Password", href="/settings?tab=security", cls=f"px-4 py-2 font-mono text-xs font-semibold rounded-lg {'bg-primary text-white' if tab == 'security' else 'text-muted hover:bg-white/5'}"),
        A("Admin & Parameters", href="/settings?tab=admin", cls=f"px-4 py-2 font-mono text-xs font-semibold rounded-lg {'bg-primary text-white' if tab == 'admin' else 'text-muted hover:bg-white/5'}") if is_coordinator else "",
        cls="flex items-center gap-2 mb-6 border-b border-white/10 pb-3"
    )

    alert = ""
    if success:
        alert = Div(icon("check_circle", "text-sm mr-2"), Span(success), cls="p-3 bg-emerald-950/40 border border-emerald-500/20 text-emerald-300 text-xs rounded-xl flex items-center mb-6")
    elif error:
        alert = Div(icon("error", "text-sm mr-2"), Span(error), cls="p-3 bg-red-950/40 border border-red-500/20 text-red-300 text-xs rounded-xl flex items-center mb-6")

    # Tab 1: Profile
    if tab == "profile":
        content = card(
            H3("Account Information", cls="font-heading font-bold text-lg mb-4"),
            Div(
                avatar(u["name"], cls="w-16 h-16 text-xl mb-4"),
                cls="flex justify-center"
            ),
            Div(
                Div(Label("Full Name", cls="block text-xs font-mono text-muted mb-1"), Input(value=u["name"], readonly=True, cls="input w-full bg-white/5 text-muted"), cls="mb-4"),
                Div(Label("Roll Number", cls="block text-xs font-mono text-muted mb-1"), Input(value=u["roll"], readonly=True, cls="input w-full bg-white/5 text-muted font-mono"), cls="mb-4"),
                Div(Label("Email Address", cls="block text-xs font-mono text-muted mb-1"), Input(value=u["email"], readonly=True, cls="input w-full bg-white/5 text-muted"), cls="mb-4"),
                Div(Label("Organizational Role", cls="block text-xs font-mono text-muted mb-1"), Input(value=f"{u['role'].replace('_', ' ').upper()} (Rank {rank})", readonly=True, cls="input w-full bg-white/5 text-muted font-mono"), cls="mb-4"),
                cls="max-w-md mx-auto"
            )
        )

    # Tab 2: Security & Password
    elif tab == "security":
        content = card(
            H3("Change Password", cls="font-heading font-bold text-lg mb-4"),
            Form(
                input_field("Current Password", "current_pw", type="password", required=True),
                input_field("New Password (Min 8 characters)", "new_pw", type="password", required=True),
                input_field("Confirm New Password", "confirm_pw", type="password", required=True),
                Div(
                    btn_primary("Update Password", type="submit", loading_text="Updating Password..."),
                    cls="flex justify-end mt-4"
                ),
                method="post",
                action="/settings/password",
                cls="max-w-md mx-auto"
            )
        )

    # Tab 3: Admin Tab (Coordinator only)
    elif tab == "admin" and is_coordinator:
        try:
            settings_rows = supabase.table("settings").select("*").execute().data or []
            cfg = {s["key"]: s["value"] for s in settings_rows}
        except Exception:
            cfg = {}

        club_name = cfg.get("club_name", "Technoverse Club")
        fiscal_term = cfg.get("fiscal_term", "2026-2027")
        threshold = cfg.get("expense_approval_threshold", "10000")

        content = card(
            H3("Club Parameters & Governance", cls="font-heading font-bold text-lg mb-4"),
            Form(
                input_field("Official Club Name", "club_name", value=club_name, required=True),
                input_field("Active Fiscal Term", "fiscal_term", value=fiscal_term, required=True),
                input_field("Expense Approval Threshold (₹ INR)", "expense_threshold", type="number", value=threshold, required=True),
                Div(
                    btn_primary("Save Parameters", type="submit", loading_text="Saving Parameters..."),
                    cls="flex justify-end mt-4"
                ),
                method="post",
                action="/settings/admin",
                cls="max-w-md mx-auto"
            )
        )
    else:
        content = card(P("Section not found.", cls="text-muted text-sm"))

    return page(session, u, "Portal Settings", header, tabs_nav, alert, content)

@rt("/settings/password", methods=["POST"])
def settings_password_post(session, current_pw: str, new_pw: str, confirm_pw: str):
    u = current_user(session)
    if not u or session.get("view_as"):
        return go("/login")

    if not check_pw(current_pw, u.get("pw_hash", "")):
        return go("/settings?tab=security&error=Current+password+is+incorrect")

    if len(new_pw) < 8:
        return go("/settings?tab=security&error=New+password+must+be+at+least+8+characters")

    if new_pw != confirm_pw:
        return go("/settings?tab=security&error=New+passwords+do+not+match")

    try:
        new_hash = hash_pw(new_pw)
        supabase.table("members").update({"pw_hash": new_hash}).eq("id", u["id"]).execute()
        invalidate_cache(f"user_{u['id']}")
        log_activity(session, "password_changed", "settings", u["id"], "User changed their password")
        return go("/settings?tab=security&success=Password+updated+successfully")
    except Exception as e:
        print("Password update error:", e)
        return go("/settings?tab=security&error=Failed+to+update+password")

@rt("/settings/admin", methods=["POST"])
def settings_admin_post(session, club_name: str, fiscal_term: str, expense_threshold: str):
    u = current_user(session)
    if not u or u["role"] not in ("club_coordinator", "president") or session.get("view_as"):
        return go("/login")

    try:
        supabase.table("settings").upsert([
            {"key": "club_name", "value": club_name.strip()},
            {"key": "fiscal_term", "value": fiscal_term.strip()},
            {"key": "expense_approval_threshold", "value": str(expense_threshold).strip()}
        ]).execute()
        invalidate_cache()
        log_activity(session, "settings_updated", "settings", None, f"Updated club parameters: {club_name.strip()}")
        return go("/settings?tab=admin&success=Club+parameters+saved+successfully")
    except Exception as e:
        print("Settings admin error:", e)
        return go("/settings?tab=admin&error=Failed+to+save+parameters")
