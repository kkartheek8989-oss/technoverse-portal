from fasthtml.common import *
from core import rt, current_user, go, supabase
from components import *
from auth import RANKS, hash_pw, can, log_activity
from cache import get_cached, set_cached, invalidate_cache

ROLES_LIST = [
    ("club_coordinator", "Club Coordinator (Superadmin - Rank 5)"),
    ("president", "President (Executive - Rank 4)"),
    ("vice_president", "Vice President (Executive - Rank 4)"),
    ("secretary", "Secretary (Minutes Head - Rank 3)"),
    ("treasurer", "Treasurer (Finance Head - Rank 3)"),
    ("technical_lead", "Technical Lead (Projects & Learning - Rank 3)"),
    ("event_coordinator", "Event Coordinator (Operations - Rank 3)"),
    ("member", "Core Member (Rank 1)")
]

ROLE_COLORS = {
    "club_coordinator": "amber",
    "president": "primary",
    "vice_president": "primary",
    "secretary": "secondary",
    "treasurer": "secondary",
    "technical_lead": "secondary",
    "event_coordinator": "secondary",
    "member": "secondary"
}

def edit_modal_for(m, u, roles_list):
    mid = m["id"]
    is_self = (m["id"] == u["id"])
    m_role = m.get("role", "member")
    
    # Filter roles: Coordinators can assign anything; Presidents can assign rank < 4
    if u["role"] == "club_coordinator":
        avail_roles = roles_list
    else:
        avail_roles = [(val, lab) for val, lab in roles_list if RANKS.get(val, 1) < 4]

    return Div(
        Div(onclick=f"document.getElementById('edit-modal-{mid}').classList.add('hidden')", cls="absolute inset-0 bg-black/75 backdrop-blur-sm"),
        card(
            Div(
                Div(
                    H3(f"Edit Core Member: {m.get('name')}", cls="font-heading font-bold text-lg text-white"),
                    P(f"Login ID: {m.get('roll')} • Current: {m_role.replace('_', ' ').title()}", cls="text-xs text-slate-400 font-mono mt-0.5"),
                    cls="flex-1"
                ),
                Button(icon("close"), onclick=f"document.getElementById('edit-modal-{mid}').classList.add('hidden')", type="button", cls="text-slate-400 hover:text-white bg-transparent border-0 cursor-pointer text-xl"),
                cls="flex items-start justify-between mb-5 pb-3 border-b border-white/[0.08]"
            ),
            Form(
                # Section 1: Member Profile Info
                Div(
                    input_field("Full Name", "name", value=m.get("name", ""), placeholder="e.g. Karthik", required=True),
                    input_field("Email Address", "email", type="email", value=m.get("email", ""), placeholder="e.g. karthik@hari.edu.in", required=True),
                    cls="grid grid-cols-1 sm:grid-cols-2 gap-3"
                ),
                Div(
                    select_field("Assigned Role", "role", avail_roles, selected=m_role),
                    select_field("Account Status", "active", [("true", "Active (Permit Portal Login)"), ("false", "Suspended (Block Login)")], selected="true" if m.get("active") else "false"),
                    cls="grid grid-cols-1 sm:grid-cols-2 gap-3"
                ),
                Div(
                    input_field("Branch / Department", "branch", value=m.get("branch", ""), placeholder="e.g. CSE-1", required=False),
                    input_field("Year of Study", "year", type="number", value=str(m.get("year", 1)), required=False),
                    cls="grid grid-cols-1 sm:grid-cols-2 gap-3"
                ),
                # Section 2: Login Credentials & Password Management
                Div(
                    Div(
                        icon("key", "text-amber-400 text-base mr-1.5"),
                        Span("Issue / Reset Login Credentials", cls="text-xs font-mono font-bold text-amber-300 uppercase tracking-wider"),
                        cls="flex items-center mb-3"
                    ),
                    input_field("Login ID / Roll Number", "roll", value=m.get("roll", ""), placeholder="e.g. 26ET103047", required=True),
                    Div(
                        Label("Set New Login Password (Overwrite)", cls="block text-xs font-mono text-slate-400 mb-1.5"),
                        Div(
                            Input(type="text", name="new_password", id=f"pw-input-{mid}", placeholder="Enter new password (or click Generate)", cls="input w-full font-mono text-xs"),
                            Button(
                                icon("casino", "text-sm mr-1"), "Generate",
                                type="button",
                                onclick=f"document.getElementById('pw-input-{mid}').value='Techno#'+Math.floor(1000+Math.random()*9000);",
                                cls="btn-ghost text-xs px-3 py-1.5 shrink-0 bg-white/5 border border-white/10 hover:bg-white/10 text-slate-300 hover:text-white rounded-lg flex items-center cursor-pointer"
                            ),
                            cls="flex items-center gap-2"
                        ),
                        P("Leave blank to keep existing password. If provided, the member can immediately sign in with this new password.", cls="text-[11px] text-slate-400 font-mono mt-1.5"),
                        cls="mb-3"
                    ),
                    cls="p-4 rounded-xl bg-amber-500/[0.04] border border-amber-500/20 mb-4"
                ),
                Div(
                    btn_ghost("Cancel", type="button", onclick=f"document.getElementById('edit-modal-{mid}').classList.add('hidden')"),
                    btn_primary(icon("save", "text-sm mr-1.5"), "Save & Issue Credentials", type="submit", loading_text="Saving Updates..."),
                    cls="flex justify-end gap-3 mt-4 pt-3 border-t border-white/[0.08]"
                ),
                method="post",
                action=f"/team/{mid}/edit"
            ),
            # Delete Action (Coordinator exclusive, cannot delete self)
            Div(
                Form(
                    btn_danger(icon("delete", "text-xs mr-1"), "Delete Member Account", type="submit", cls="text-xs py-1.5 px-3"),
                    method="post",
                    action=f"/team/{mid}/delete",
                    onsubmit="return confirm('Are you sure you want to permanently delete this member account? This action cannot be undone.');",
                    cls="inline-block"
                ) if u["role"] == "club_coordinator" and not is_self else "",
                cls="mt-3 flex justify-start"
            ) if u["role"] == "club_coordinator" and not is_self else "",
            cls="relative z-10 w-full max-w-xl mx-auto mt-6 max-h-[90vh] overflow-y-auto border border-blue-500/30 bg-[#0f172a] shadow-2xl"
        ),
        id=f"edit-modal-{mid}",
        cls="fixed inset-0 z-50 flex items-center justify-center p-4 hidden"
    )

@rt("/team", methods=["GET"])
def team_get(session, role_filter: str = "all", search: str = "", msg: str = "", error: str = ""):
    u = current_user(session)
    if not u:
        return go("/login")
    role = session.get("view_as") or u["role"]
    rank = RANKS.get(role, 1)

    members = get_cached("team_members", ttl=30)
    if members is None:
        try:
            members = supabase.table("members").select("*").order("created_at", desc=False).execute().data or []
            set_cached("team_members", members)
        except Exception as e:
            print("Members fetch error:", e)
            members = []

    # Sort by rank descending
    members.sort(key=lambda m: RANKS.get(m.get("role"), 1), reverse=True)

    if role_filter != "all":
        members = [m for m in members if m.get("role") == role_filter]
    if search:
        s = search.lower().strip()
        members = [m for m in members if s in (m.get("name") or "").lower() or s in (m.get("roll") or "").lower() or s in (m.get("email") or "").lower()]

    # Account creation & full management is restricted to Club Coordinator and President
    can_provision_accounts = (u["role"] in ("club_coordinator", "president")) and not session.get("view_as")

    def member_card(m):
        m_role = m.get("role", "member")
        m_rank = RANKS.get(m_role, 1)
        can_manage_member = (u["role"] == "club_coordinator") or (u["role"] == "president" and m_rank < 4)
        is_self = (m["id"] == u["id"])

        role_badge = badge(f"{m_role.replace('_', ' ').upper()} (R{m_rank})", ROLE_COLORS.get(m_role, "secondary"))
        status_badge = "" if m.get("active", True) else badge("SUSPENDED", "urgent")

        return card(
            Div(
                Div(
                    avatar(m.get("name", "?"), cls="w-11 h-11 text-xs shrink-0"),
                    Div(
                        H3(m.get("name", "Unknown"), cls="font-heading font-bold text-sm leading-snug truncate"),
                        P(m.get("roll", ""), cls="font-mono text-[11px] text-slate-400 font-bold mt-0.5"),
                        cls="flex-1 min-w-0"
                    ),
                    cls="flex items-center gap-3 min-w-0 flex-1"
                ),
                Div(
                    status_badge,
                    role_badge,
                    cls="flex items-center gap-1.5 shrink-0 mt-2 sm:mt-0"
                ),
                cls="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4"
            ),
            Div(
                Div(icon("mail", "text-xs text-muted mr-1.5"), Span(m.get("email", ""), cls="text-xs text-secondary truncate"), cls="flex items-center mb-1"),
                Div(icon("school", "text-xs text-muted mr-1.5"), Span(f"Branch: {m.get('branch') or 'General'} • Year {m.get('year') or 'N/A'}", cls="text-xs text-muted"), cls="flex items-center"),
                cls="pt-3 border-t border-white/5 space-y-1"
            ),
            Div(
                Button(
                    icon("edit", "text-xs mr-1 text-blue-400"), "Edit Profile & Credentials",
                    type="button",
                    onclick=f"document.getElementById('edit-modal-{m['id']}').classList.remove('hidden')",
                    cls="w-full text-xs py-1.5 px-3 rounded-lg border border-blue-500/25 bg-blue-500/10 hover:bg-blue-500/20 text-blue-300 hover:text-white transition-all flex items-center justify-center font-medium cursor-pointer"
                ),
                cls="mt-3 pt-3 border-t border-white/[0.06]"
            ) if can_manage_member and not session.get("view_as") else "",
            p="p-5",
            cls="hover:border-white/20 transition-all flex flex-col justify-between"
        )

    # Provision modal for Coordinator and President
    avail_provision_roles = ROLES_LIST if u["role"] == "club_coordinator" else [(val, lab) for val, lab in ROLES_LIST if RANKS.get(val, 1) < 4]

    modal = Div(
        Div(onclick="document.getElementById('member-modal').classList.add('hidden')", cls="absolute inset-0 bg-black/60 backdrop-blur-sm"),
        card(
            Div(
                Div(
                    H3("Provision Core Team Member", cls="font-heading font-bold text-xl text-white"),
                    P("Coordinator & Executive Provisioning Desk", cls="text-xs text-amber-400 font-mono mt-0.5")
                ),
                Button(icon("close"), onclick="document.getElementById('member-modal').classList.add('hidden')", type="button", cls="text-muted hover:text-white bg-transparent border-0 cursor-pointer"),
                cls="flex items-center justify-between mb-4"
            ),
            Form(
                input_field("Full Name", "name", placeholder="e.g. Rahul Sharma", required=True),
                Div(
                    input_field("Login ID (Roll Number)", "roll", placeholder="e.g. 26ET104011", required=True),
                    input_field("Email Address", "email", type="email", placeholder="rahul@hari.edu.in", required=True),
                    cls="grid grid-cols-1 sm:grid-cols-2 gap-3"
                ),
                Div(
                    select_field("Assigned Role", "role", avail_provision_roles),
                    Div(
                        Label("Initial Login Password", cls="block text-xs font-mono text-slate-400 mb-1.5"),
                        Div(
                            Input(name="password", id="new-member-pw", type="text", placeholder="Enter password", value="Techno#2026", required=True, cls="input w-full font-mono text-xs"),
                            Button(
                                icon("casino", "text-sm mr-1"), "Generate",
                                type="button",
                                onclick="document.getElementById('new-member-pw').value='Techno#'+Math.floor(1000+Math.random()*9000);",
                                cls="btn-ghost text-xs px-3 py-1.5 shrink-0 bg-white/5 border border-white/10 hover:bg-white/10 text-slate-300 hover:text-white rounded-lg flex items-center cursor-pointer"
                            ),
                            cls="flex items-center gap-2"
                        ),
                        cls="mb-4"
                    ),
                    cls="grid grid-cols-1 sm:grid-cols-2 gap-3"
                ),
                Div(
                    input_field("Branch / Dept", "branch", placeholder="e.g. CSE-1 / CSM-2", required=False),
                    input_field("Year of Study", "year", type="number", value="2", required=False),
                    cls="grid grid-cols-1 sm:grid-cols-2 gap-3"
                ),
                Div(
                    btn_ghost("Cancel", type="button", onclick="document.getElementById('member-modal').classList.add('hidden')"),
                    btn_primary(icon("person_add", "text-sm mr-1"), "Create Account & Issue Credentials", type="submit", loading_text="Provisioning Account..."),
                    cls="flex justify-end gap-3 mt-6 pt-3 border-t border-white/[0.08]"
                ),
                method="post",
                action="/team/new"
            ),
            cls="relative z-10 w-full max-w-lg mx-auto mt-12 max-h-[90vh] overflow-y-auto"
        ),
        id="member-modal",
        cls="fixed inset-0 z-50 flex items-center justify-center p-4 hidden"
    )

    # Edit modals for all editable members
    edit_modals = [
        edit_modal_for(m, u, ROLES_LIST)
        for m in members
        if ((u["role"] == "club_coordinator") or (u["role"] == "president" and RANKS.get(m.get("role"), 1) < 4))
    ]

    header = Div(
        Div(
            H1("Core Team Directory", cls="font-heading font-bold text-2xl"),
            P("Active club leadership, department heads, and appointed committee members", cls="text-sm text-secondary"),
            cls="flex-1"
        ),
        Div(
            btn_primary(
                icon("person_add", "text-sm"), "Provision Member",
                onclick="document.getElementById('member-modal').classList.remove('hidden')",
                type="button"
            ) if can_provision_accounts else "",
            cls="flex items-center gap-3"
        ),
        cls="flex flex-wrap items-center justify-between gap-4 mb-6"
    )

    alerts_div = Div(
        Div(
            Div(icon("check_circle", "text-emerald-400 mr-2"), Span(msg), cls="flex items-center text-emerald-200 text-sm font-semibold"),
            cls="bg-emerald-950/60 border border-emerald-500/40 p-4 rounded-xl mb-6 shadow-xl"
        ) if msg else "",
        Div(
            Div(icon("error", "text-red-400 mr-2"), Span(error), cls="flex items-center text-red-200 text-sm font-semibold"),
            cls="bg-red-950/60 border border-red-500/40 p-4 rounded-xl mb-6 shadow-xl"
        ) if error else "",
    )

    stats = Div(
        stat_card("Total Committee", len(members), "badge"),
        stat_card("Executive Board", sum(1 for m in members if RANKS.get(m.get("role"), 1) >= 4), "military_tech"),
        stat_card("Section Leads", sum(1 for m in members if RANKS.get(m.get("role"), 1) == 3), "supervised_user_circle"),
        cls="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6"
    )

    grid = Div(
        *[member_card(m) for m in members] or [
            Div(P("No members found matching your search.", cls="text-muted text-sm text-center py-12"), cls="col-span-full")
        ],
        cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
    )

    return page(session, u, "Core Team", header, alerts_div, stats, grid, modal, *edit_modals)

@rt("/team/new", methods=["POST"])
def team_new_post(session, name: str, roll: str, email: str, role: str, password: str, branch: str = "", year: int = 1):
    u = current_user(session)
    if not u or session.get("view_as"):
        return go("/login")
    
    # Account creation is strictly restricted to Club Coordinator & President
    if u["role"] not in ("club_coordinator", "president"):
        return go("/team")

    target_rank = RANKS.get(role, 1)
    if target_rank >= 4 and u["role"] != "club_coordinator":
        return go("/team?error=Presidents+cannot+provision+accounts+at+or+above+executive+level.")

    clean_name = name.strip()
    clean_roll = roll.strip().upper()
    clean_email = email.strip().lower()
    clean_pw = password.strip()

    if not clean_name or not clean_roll or not clean_email or not clean_pw:
        return go("/team?error=Name,+Roll+Number,+Email,+and+Password+are+required.")

    if len(clean_pw) < 6:
        return go("/team?error=Password+must+be+at+least+6+characters.")

    payload = {
        "name": clean_name,
        "roll": clean_roll,
        "email": clean_email,
        "role": role,
        "pw_hash": hash_pw(clean_pw),
        "branch": branch.strip() if branch else None,
        "year": int(year or 1),
        "active": True
    }

    try:
        res = supabase.table("members").insert(payload).execute()
        invalidate_cache("team_")
        invalidate_cache("user_")
        invalidate_cache("members_")
        if res.data:
            log_activity(session, "member_provisioned", "team", res.data[0]["id"], f"Provisioned member: {clean_name} ({role})")
        return go(f"/team?msg=Member+'{clean_name}'+successfully+provisioned!+Login+ID:+{clean_roll}+|+Initial+Password:+{clean_pw}")
    except Exception as e:
        print("Member provision error:", e)
        return go(f"/team?error=Failed+to+provision+member:+{str(e)[:80]}")

@rt("/team/{mid}/edit", methods=["POST"])
def team_edit_post(session, mid: str, name: str, roll: str, email: str, role: str, branch: str = "", year: int = 1, active: str = "true", new_password: str = ""):
    u = current_user(session)
    if not u or session.get("view_as"):
        return go("/login")

    # Only Coordinator or President can edit
    if u["role"] not in ("club_coordinator", "president"):
        return go("/team")

    target_rank = RANKS.get(role, 1)
    if u["role"] == "president" and target_rank >= 4:
        return go("/team?error=Presidents+can+only+modify+ranks+below+executive+level.")

    clean_name = name.strip()
    clean_roll = roll.strip().upper()
    clean_email = email.strip().lower()

    if not clean_name or not clean_roll or not clean_email:
        return go("/team?error=Name,+Roll+Number+(Login+ID),+and+Email+are+required.")

    payload = {
        "name": clean_name,
        "roll": clean_roll,
        "email": clean_email,
        "role": role,
        "branch": branch.strip() if branch else None,
        "year": int(year or 1),
        "active": (active == "true")
    }

    issued_pw_note = ""
    if new_password and len(new_password.strip()) >= 6:
        clean_pw = new_password.strip()
        payload["pw_hash"] = hash_pw(clean_pw)
        issued_pw_note = f" | New Issued Password: {clean_pw}"

    try:
        supabase.table("members").update(payload).eq("id", mid).execute()
        invalidate_cache("team_")
        invalidate_cache(f"user_{mid}")
        invalidate_cache("members_")
        log_activity(session, "member_modified", "team", mid, f"Updated member {clean_name} (Login ID: {clean_roll})")
        return go(f"/team?msg=Member+'{clean_name}'+successfully+updated!+Login+ID:+{clean_roll}{issued_pw_note}")
    except Exception as e:
        print("Member edit error:", e)
        return go(f"/team?error=Failed+to+update+member:+{str(e)[:80]}")

@rt("/team/{mid}/role", methods=["POST"])
def team_update_role(session, mid: str, new_role: str):
    u = current_user(session)
    if not u or session.get("view_as"):
        return go("/login")
    if u["role"] not in ("club_coordinator", "president"):
        return go("/team")

    target_rank = RANKS.get(new_role, 1)
    if target_rank >= 4 and u["role"] != "club_coordinator":
        return go("/team")

    try:
        supabase.table("members").update({"role": new_role}).eq("id", mid).execute()
        invalidate_cache("team_")
        invalidate_cache("user_")
        invalidate_cache("members_")
        log_activity(session, "role_changed", "team", mid, f"Updated role to {new_role}")
    except Exception as e:
        print("Role update error:", e)

    return go("/team")

@rt("/team/{mid}/delete", methods=["POST"])
def team_delete_post(session, mid: str):
    u = current_user(session)
    if not u or session.get("view_as") or u["role"] != "club_coordinator":
        return go("/team")
    if str(u["id"]) == str(mid):
        return go("/team?error=Cannot+delete+your+own+coordinator+account.")

    try:
        supabase.table("members").delete().eq("id", mid).execute()
        invalidate_cache("team_")
        invalidate_cache("user_")
        invalidate_cache("members_")
        log_activity(session, "member_deleted", "team", mid, f"Coordinator permanently deleted member #{mid}")
        return go("/team?msg=Member+account+permanently+deleted.")
    except Exception as e:
        print("Member delete error:", e)
        # Foreign key safeguard: deactivate if cannot delete directly
        try:
            supabase.table("members").update({"active": False}).eq("id", mid).execute()
            invalidate_cache("team_")
            invalidate_cache("user_")
            invalidate_cache("members_")
            return go("/team?msg=Member+has+associated+records;+account+has+been+deactivated+instead.")
        except Exception as e2:
            return go(f"/team?error=Failed+to+delete+member:+{str(e2)[:80]}")
