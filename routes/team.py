from fasthtml.common import *
from core import rt, current_user, go, supabase
from components import *
from auth import RANKS, hash_pw, can, log_activity

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

@rt("/team", methods=["GET"])
def team_get(session, role_filter: str = "all", search: str = ""):
    u = current_user(session)
    if not u:
        return go("/login")
    role = session.get("view_as") or u["role"]
    rank = RANKS.get(role, 1)

    try:
        members = supabase.table("members").select("*").order("created_at", desc=False).execute().data or []
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

    def member_card(m):
        m_role = m.get("role", "member")
        m_rank = RANKS.get(m_role, 1)
        can_manage = (rank == 5) or (rank >= 4 and m_rank < 4)
        is_self = (m["id"] == u["id"])

        role_form = Form(
            Select(
                *[Option(label.split(" (")[0], value=val, selected=(val == m_role)) for val, label in ROLES_LIST],
                name="new_role",
                onchange="this.form.submit()",
                cls="input text-xs py-1 px-2 font-mono bg-dark"
            ),
            method="post",
            action=f"/team/{m['id']}/role",
            cls="inline-block"
        ) if can_manage and not is_self and not session.get("view_as") else (
            badge(f"{m_role.replace('_', ' ').upper()} (R{m_rank})", ROLE_COLORS.get(m_role, "secondary"))
        )

        return card(
            Div(
                avatar(m.get("name", "?"), cls="w-12 h-12 text-sm"),
                Div(
                    H3(m.get("name", "Unknown"), cls="font-heading font-bold text-base leading-tight"),
                    P(m.get("roll", ""), cls="font-mono text-xs text-muted font-bold mt-0.5"),
                    cls="flex-1 min-w-0"
                ),
                role_form,
                cls="flex items-center gap-3 mb-4"
            ),
            Div(
                Div(icon("mail", "text-xs text-muted mr-1.5"), Span(m.get("email", ""), cls="text-xs text-secondary truncate"), cls="flex items-center mb-1"),
                Div(icon("school", "text-xs text-muted mr-1.5"), Span(f"Branch: {m.get('branch') or 'General'} • Year {m.get('year') or 'N/A'}", cls="text-xs text-muted"), cls="flex items-center"),
                cls="pt-3 border-t border-white/5 space-y-1"
            ),
            p="p-5",
            cls="hover:border-white/20 transition-all flex flex-col justify-between"
        )

    modal = Div(
        Div(onclick="document.getElementById('member-modal').classList.add('hidden')", cls="absolute inset-0 bg-black/60 backdrop-blur-sm"),
        card(
            Div(
                H3("Add Core Team Member", cls="font-heading font-bold text-xl"),
                Button(icon("close"), onclick="document.getElementById('member-modal').classList.add('hidden')", type="button", cls="text-muted hover:text-white bg-transparent border-0 cursor-pointer"),
                cls="flex items-center justify-between mb-4"
            ),
            Form(
                input_field("Full Name", "name", placeholder="e.g. Rahul Sharma", required=True),
                Div(
                    input_field("Roll Number", "roll", placeholder="e.g. 26ET104011", required=True),
                    input_field("Email Address", "email", type="email", placeholder="rahul@college.edu", required=True),
                    cls="grid grid-cols-2 gap-3"
                ),
                Div(
                    select_field("Assigned Role", "role", ROLES_LIST),
                    input_field("Login Password", "password", type="password", placeholder="Min 8 characters", required=True),
                    cls="grid grid-cols-2 gap-3"
                ),
                Div(
                    input_field("Branch / Dept", "branch", placeholder="e.g. CSE / IT / ECE", required=False),
                    input_field("Year of Study", "year", type="number", value="2", required=False),
                    cls="grid grid-cols-2 gap-3"
                ),
                Div(
                    btn_ghost("Cancel", type="button", onclick="document.getElementById('member-modal').classList.add('hidden')"),
                    btn_primary("Create Member Account", type="submit"),
                    cls="flex justify-end gap-3 mt-6"
                ),
                method="post",
                action="/team/new"
            ),
            cls="relative z-10 w-full max-w-lg mx-auto mt-12 max-h-[90vh] overflow-y-auto"
        ),
        id="member-modal",
        cls="fixed inset-0 z-50 flex items-center justify-center p-4 hidden"
    )

    header = Div(
        Div(
            H1("Core Team Directory", cls="font-heading font-bold text-2xl"),
            P("Active club leadership, department heads, and core members", cls="text-sm text-secondary"),
            cls="flex-1"
        ),
        Div(
            btn_primary(
                icon("person_add", "text-sm"), "Add Member",
                onclick="document.getElementById('member-modal').classList.remove('hidden')",
                type="button"
            ) if rank >= 4 and not session.get("view_as") else "",
            cls="flex items-center gap-3"
        ),
        cls="flex flex-wrap items-center justify-between gap-4 mb-6"
    )

    stats = Div(
        stat_card("Total Members", len(members), "badge"),
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

    return page(session, u, "Core Team", header, stats, grid, modal)

@rt("/team/new", methods=["POST"])
def team_new_post(session, name: str, roll: str, email: str, role: str, password: str, branch: str = "", year: int = 1):
    u = current_user(session)
    if not u or session.get("view_as"):
        return go("/login")
    if RANKS.get(u["role"], 1) < 4:
        return go("/team")
    # Only club_coordinator can create rank 4+ accounts
    target_rank = RANKS.get(role, 1)
    if target_rank >= 4 and u["role"] != "club_coordinator":
        return go("/team")

    if len(password) < 8:
        return go("/team")

    payload = {
        "name": name.strip(),
        "roll": roll.strip().upper(),
        "email": email.strip().lower(),
        "role": role,
        "pw_hash": hash_pw(password),
        "branch": branch.strip() if branch else None,
        "year": int(year or 1),
        "active": True
    }

    try:
        res = supabase.table("members").insert(payload).execute()
        if res.data:
            log_activity(session, "member_created", "team", res.data[0]["id"], f"Created member: {name.strip()} ({role})")
    except Exception as e:
        print("Member creation error:", e)

    return go("/team")

@rt("/team/{mid}/role", methods=["POST"])
def team_update_role(session, mid: str, new_role: str):
    u = current_user(session)
    if not u or session.get("view_as"):
        return go("/login")
    if RANKS.get(u["role"], 1) < 4:
        return go("/team")

    target_rank = RANKS.get(new_role, 1)
    if target_rank >= 4 and u["role"] != "club_coordinator":
        return go("/team")

    try:
        supabase.table("members").update({"role": new_role}).eq("id", mid).execute()
        log_activity(session, "role_changed", "team", mid, f"Updated role to {new_role}")
    except Exception as e:
        print("Role update error:", e)

    return go("/team")
