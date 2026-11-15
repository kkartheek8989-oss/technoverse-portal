from datetime import datetime, timedelta, timezone
from fasthtml.common import *
from core import rt, current_user, go, supabase
from components import *
from auth import RANKS, can, log_activity

@rt("/", methods=["GET"])
def dashboard_get(session):
    u = current_user(session)
    if not u:
        return go("/login")
    role = session.get("view_as") or u["role"]
    rank = RANKS.get(role, 1)
    
    try:
        tasks = supabase.table("tasks").select("id,code,title,status,assigned_to,due_at").execute().data or []
    except Exception as e:
        print("Warning: tasks fetch failed:", e)
        tasks = []

    mine = [t for t in tasks if t.get("assigned_to") == u["id"] and t.get("status") != "done"]
    
    since = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
    try:
        act = supabase.table("activity").select("member_id").gte("created_at", since).execute().data or []
    except Exception as e:
        print("Warning: activity fetch failed:", e)
        act = []

    try:
        anns = supabase.table("announcements").select("*").order("pinned", desc=True).order("created_at", desc=True).limit(5).execute().data or []
    except Exception as e:
        print("Warning: announcements fetch failed:", e)
        anns = []

    stat = lambda k, v: card(Div(k, cls="text-xs text-muted font-mono"), Div(str(v), cls="text-2xl font-mono font-bold mt-1"))
    row = lambda t: Div(
        Div(
            Div(t.get("title", ""), cls="text-sm font-semibold"),
            Div(f"#TK-{t.get('code', '')}", cls="text-xs text-muted font-mono")
        ),
        Form(btn_ghost("Mark complete", cls="text-xs"), method="post", action=f"/tasks/{t['id']}/done"),
        cls="flex items-center justify-between p-3 rounded-lg bg-white/5"
    )
    
    view_as = Form(
        Select(
            *[Option(r.replace("_", " ").title(), value=r) for r in RANKS if RANKS[r] < RANKS[u["role"]] or r == u["role"]],
            name="role", cls="input text-xs"
        ),
        btn_ghost("Preview as", cls="text-xs"),
        method="post", action="/view-as", cls="flex gap-2"
    ) if RANKS.get(u["role"], 1) >= 4 and not session.get("view_as") else ""

    return page(
        session, u, "Dashboard",
        Div(
            Div(
                H1(f"Hello, {u['name']}", cls="font-heading font-bold text-2xl"),
                P("Code • Innovate • Secure • Transform", cls="text-sm text-secondary"),
                cls="flex-1"
            ),
            view_as,
            cls="flex flex-wrap items-center justify-between gap-3 mb-6"
        ),
        Div(
            stat("Total tasks", len(tasks)),
            stat("My open tasks", len(mine)),
            stat("Active in last 15 min", len({a["member_id"] for a in act if a.get("member_id")})),
            cls="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6"
        ),
        card(
            H3("Announcements", cls="font-heading font-semibold mb-3"),
            *[Div(
                P(a.get("body", ""), cls="text-sm"),
                P((a.get("created_at") or "")[:10], cls="text-[10px] text-muted font-mono"),
                cls="p-3 rounded-lg bg-white/5 mb-2"
            ) for a in anns] or [P("No announcements yet.", cls="text-sm text-muted")]
        ),
        H3("My open tasks", cls="font-heading font-semibold mt-8 mb-3"),
        Div(*[row(t) for t in mine] or [P("No open tasks.", cls="text-sm text-muted")], cls="space-y-2"),
        H3("Quick actions", cls="font-heading font-semibold mt-8 mb-3"),
        Div(
            A(btn_primary("Tasks", cls="w-full"), href="/tasks"),
            A(btn_primary("Events", cls="w-full") if can(role, "events", "create") else btn_ghost("Events", cls="w-full"), href="/events"),
            A(btn_primary("Files", cls="w-full"), href="/files"),
            cls="grid grid-cols-1 md:grid-cols-3 gap-3"
        )
    )

@rt("/tasks/{tid}/done", methods=["POST"])
def task_done(session, tid: int):
    u = current_user(session)
    if not u:
        return go("/login")
    if session.get("view_as"):
        return go("/")
    q = supabase.table("tasks").update({"status": "done"}).eq("id", tid)
    if RANKS.get(u["role"], 1) < 3:
        q = q.eq("assigned_to", u["id"])
    res = q.execute()
    if res.data:
        log_activity(session, "task_done", "tasks", tid, res.data[0].get("title", ""))
    return go("/")

@rt("/view-as", methods=["POST"])
def view_as(session, role: str):
    u = current_user(session)
    if not u or RANKS.get(u["role"], 1) < 4 or role not in RANKS or RANKS[role] > RANKS[u["role"]]:
        return go("/")
    session["view_as"] = role if role != u["role"] else None
    log_activity(session, "view_as_started", "auth", None, f"Previewing as {role}")
    return go("/")

@rt("/view-as/reset", methods=["POST"])
def view_as_reset(session):
    if session.get("view_as"):
        log_activity(session, "view_as_ended", "auth", None, "Preview ended")
    session["view_as"] = None
    return go("/")
