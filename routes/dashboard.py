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

    # 1. Fetch Tasks
    try:
        tasks = supabase.table("tasks").select("id,code,title,status,assigned_to,due_at").execute().data or []
    except Exception as e:
        print("Warning: tasks fetch failed:", e)
        tasks = []

    mine = [t for t in tasks if t.get("assigned_to") == u["id"] and t.get("status") != "done"]

    # 2. Fetch Recent Activity
    since = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
    try:
        act = supabase.table("activity").select("member_id").gte("created_at", since).execute().data or []
    except Exception as e:
        print("Warning: activity fetch failed:", e)
        act = []

    # 3. Fetch Announcements
    try:
        anns = supabase.table("announcements").select("*").order("pinned", desc=True).order("created_at", desc=True).limit(5).execute().data or []
    except Exception as e:
        print("Warning: announcements fetch failed:", e)
        anns = []

    # 4. Fetch Flagship Events
    try:
        events = supabase.table("events").select("*").order("starts_at", desc=False).limit(3).execute().data or []
    except Exception:
        events = []

    # Default announcements if empty
    if not anns:
        anns = [
            {"body": "🚀 CodeX 2026 National Hackathon registrations are officially open! Check the Events tab for tracks and prizes.", "created_at": "2026-11-15T10:00:00Z", "pinned": True},
            {"body": "📚 New technical curriculum on LLM Multi-Agent Swarms & FastHTML published to the Learning Hub.", "created_at": "2026-11-14T14:30:00Z", "pinned": False}
        ]

    task_row = lambda t: Div(
        Div(
            Div(t.get("title", ""), cls="text-sm font-semibold"),
            Div(f"#TK-{t.get('code', t.get('id'))}", cls="text-xs text-muted font-mono"),
            cls="flex-1 min-w-0 mr-3"
        ),
        Form(
            btn_ghost("Mark complete", icon("check", "text-xs"), cls="text-xs py-1 px-3"),
            method="post", action=f"/tasks/{t['id']}/done"
        ),
        cls="flex items-center justify-between p-3.5 rounded-xl bg-white/5 hover:bg-white/10 transition-colors"
    )

    view_as = Form(
        Select(
            *[Option(r.replace("_", " ").title(), value=r) for r in RANKS if RANKS[r] < RANKS.get(u["role"], 1) or r == u["role"]],
            name="role", cls="input text-xs py-1.5 px-3 bg-dark font-mono"
        ),
        btn_ghost("Preview Role", cls="text-xs py-1.5 px-3"),
        method="post", action="/view-as", cls="flex items-center gap-2"
    ) if RANKS.get(u["role"], 1) >= 4 and not session.get("view_as") else ""

    # Hero Banner
    hero_banner = card(
        Div(
            Div(
                Div(
                    badge("HARI UNIVERSITY", "amber"),
                    badge("OFFICIAL TECHNICAL BODY", "primary"),
                    cls="flex flex-wrap items-center gap-2 mb-3"
                ),
                H1(f"Welcome back, {u['name']}", cls="font-heading font-extrabold text-3xl sm:text-4xl text-white mb-2 leading-tight"),
                P("Code • Innovate • Secure • Transform", cls="text-sm font-mono text-amber font-semibold tracking-wide uppercase mb-3"),
                P(
                    "Empowering next-generation engineers, researchers, and builders at Hari University through "
                    "high-impact technical development, competitive hackathons, and industry-grade engineering tracks.",
                    cls="text-sm text-secondary leading-relaxed max-w-2xl"
                ),
                cls="flex-1"
            ),
            Div(
                Img(src="/logo-full.png", alt="Technoverse Club Logo", cls="w-48 sm:w-60 bg-white p-3 rounded-2xl shadow-2xl shrink-0 hidden lg:block"),
                cls="shrink-0"
            ),
            cls="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6"
        ),
        cls="bg-gradient-to-br from-[#0f1a3d] via-[#091330] to-[#070d24] border-primary/30 p-6 sm:p-8 mb-8"
    )

    # Core Pillars Section
    pillars = Div(
        card(
            Div(icon("code", "text-primary text-2xl mb-3")),
            H4("Software & Systems", cls="font-heading font-bold text-base mb-1.5"),
            P("Building scalable full-stack applications, open-source utilities, and developer tooling.", cls="text-xs text-secondary leading-relaxed"),
            p="p-5"
        ),
        card(
            Div(icon("smart_toy", "text-amber text-2xl mb-3")),
            H4("AI & Machine Learning", cls="font-heading font-bold text-base mb-1.5"),
            P("Autonomous agentic swarms, fine-tuned neural models, and enterprise RAG pipelines.", cls="text-xs text-secondary leading-relaxed"),
            p="p-5"
        ),
        card(
            Div(icon("security", "text-emerald-400 text-2xl mb-3")),
            H4("Cyber Defense & CTF", cls="font-heading font-bold text-base mb-1.5"),
            P("Offensive security research, ethical penetration testing, and national security challenges.", cls="text-xs text-secondary leading-relaxed"),
            p="p-5"
        ),
        card(
            Div(icon("cloud", "text-blue-400 text-2xl mb-3")),
            H4("Cloud & Infrastructure", cls="font-heading font-bold text-base mb-1.5"),
            P("Microservices, containerization, distributed databases, and high-availability operations.", cls="text-xs text-secondary leading-relaxed"),
            p="p-5"
        ),
        cls="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
    )

    # Stat Metrics
    stats = Div(
        stat_card("Total Deliverables", len(tasks), "checklist", "Active across all sprints"),
        stat_card("My Open Tasks", len(mine), "pending_actions", "Assigned to your queue"),
        stat_card("Active Members", len({a["member_id"] for a in act if a.get("member_id")}) or 1, "people", "Logged in last 15 min"),
        cls="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8"
    )

    # Flagship Events Row
    def event_snippet(ev):
        start_date = (ev.get("starts_at") or "")[:10]
        return Div(
            Div(
                badge(ev.get("flagship", "Flagship").upper(), "amber" if ev.get("flagship") != "none" else "primary"),
                Span(start_date, cls="text-xs font-mono text-muted"),
                cls="flex items-center justify-between mb-2"
            ),
            H4(ev.get("title", "Flagship Event"), cls="font-semibold text-sm mb-1"),
            P(ev.get("description", "") or "Join the campus technical challenge.", cls="text-xs text-secondary line-clamp-2 mb-3"),
            Div(
                Span(f"📍 {ev.get('venue') or 'Campus Auditorium'}", cls="text-[11px] text-muted truncate"),
                A("View Details →", href="/events", cls="text-xs font-bold text-primary hover:underline ml-auto"),
                cls="flex items-center justify-between pt-2 border-t border-white/5"
            ),
            cls="p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-colors"
        )

    events_section = card(
        Div(
            H3("Upcoming Flagship Summits", cls="font-heading font-bold text-lg"),
            A("Browse All Events →", href="/events", cls="text-xs text-primary hover:underline font-mono"),
            cls="flex items-center justify-between mb-4"
        ),
        Div(
            *[event_snippet(e) for e in events] or [P("No upcoming events scheduled.", cls="text-muted text-sm py-4 text-center")],
            cls="grid grid-cols-1 md:grid-cols-3 gap-4"
        ),
        cls="mb-8"
    )

    # Announcements Card
    announcements_card = card(
        Div(
            H3("Official Announcements", cls="font-heading font-bold text-lg"),
            icon("campaign", "text-amber text-xl"),
            cls="flex items-center justify-between mb-4"
        ),
        Div(
            *[Div(
                P(a.get("body", ""), cls="text-sm text-secondary leading-relaxed"),
                Div(
                    badge("PINNED", "amber") if a.get("pinned") else "",
                    Span(f"Date: {(a.get('created_at') or '')[:10]}", cls="text-[10px] text-muted font-mono"),
                    cls="flex items-center justify-between mt-2 pt-2 border-t border-white/5"
                ),
                cls="p-3.5 rounded-xl bg-white/5 mb-3"
            ) for a in anns],
            cls="space-y-1"
        )
    )

    # My Tasks Card
    my_tasks_card = card(
        Div(
            H3("My Open Deliverables", cls="font-heading font-bold text-lg"),
            A("Full Kanban Board →", href="/tasks", cls="text-xs text-primary hover:underline font-mono"),
            cls="flex items-center justify-between mb-4"
        ),
        Div(
            *[task_row(t) for t in mine] or [
                Div(
                    icon("check_circle", "text-emerald-400 text-3xl mb-2"),
                    P("All caught up! No pending tasks assigned to you.", cls="text-sm text-secondary font-medium"),
                    cls="text-center py-8 bg-white/5 rounded-xl"
                )
            ],
            cls="space-y-2"
        )
    )

    bottom_grid = Div(
        my_tasks_card,
        announcements_card,
        cls="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8"
    )

    # Quick Navigation Actions
    quick_actions = Div(
        H3("Quick Navigation Hub", cls="font-heading font-bold text-lg mb-4"),
        Div(
            A(btn_primary(icon("checklist", "text-sm"), "Tasks Board", cls="w-full py-3"), href="/tasks"),
            A(btn_primary(icon("calendar_month", "text-sm"), "Events & Summits", cls="w-full py-3"), href="/events"),
            A(btn_primary(icon("school", "text-sm"), "Learning Tracks", cls="w-full py-3"), href="/learning"),
            A(btn_primary(icon("account_balance_wallet", "text-sm"), "Club Finance", cls="w-full py-3"), href="/finance"),
            cls="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
        )
    )

    return page(
        session, u, "Home",
        Div(view_as, cls="flex justify-end mb-4") if view_as else "",
        hero_banner,
        pillars,
        stats,
        events_section,
        bottom_grid,
        quick_actions
    )

@rt("/tasks/{tid}/done", methods=["POST"])
def task_done(session, tid: int):
    u = current_user(session)
    if not u or session.get("view_as"):
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
    if not u or RANKS.get(u["role"], 1) < 4 or role not in RANKS or RANKS[role] > RANKS.get(u["role"], 1):
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
