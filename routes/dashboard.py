from datetime import datetime, timedelta, timezone
from fasthtml.common import *
from core import rt, current_user, go, supabase
from components import *
from auth import RANKS, can, log_activity
from site_config import get_site_config
from cache import get_cached, set_cached, invalidate_cache

@rt("/", methods=["GET"])
def dashboard_get(session):
    u = current_user(session)
    if not u:
        return go("/login")
    role = session.get("view_as") or u["role"]
    rank = RANKS.get(role, 1)

    # 1. Fetch Tasks (cached 15s)
    tasks = get_cached("dashboard_tasks", ttl=15)
    if tasks is None:
        try:
            tasks = supabase.table("tasks").select("id,code,title,status,assigned_to,due_at").execute().data or []
            set_cached("dashboard_tasks", tasks)
        except Exception as e:
            print("Warning: tasks fetch failed:", e)
            tasks = []

    mine = [t for t in tasks if t.get("assigned_to") == u["id"] and t.get("status") != "done"]

    # 2. Fetch Recent Activity (cached 20s)
    act = get_cached("dashboard_act", ttl=20)
    if act is None:
        since = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
        try:
            act = supabase.table("activity").select("member_id").gte("created_at", since).execute().data or []
            set_cached("dashboard_act", act)
        except Exception as e:
            print("Warning: activity fetch failed:", e)
            act = []

    # 3. Fetch Announcements (cached 30s)
    anns = get_cached("dashboard_anns", ttl=30)
    if anns is None:
        try:
            anns = supabase.table("announcements").select("*").order("pinned", desc=True).order("created_at", desc=True).limit(5).execute().data or []
            set_cached("dashboard_anns", anns)
        except Exception as e:
            print("Warning: announcements fetch failed:", e)
            anns = []

    # 4. Fetch Flagship Events (cached 30s)
    events = get_cached("dashboard_events", ttl=30)
    if events is None:
        try:
            events = supabase.table("events").select("*").order("starts_at", desc=False).limit(3).execute().data or []
            set_cached("dashboard_events", events)
        except Exception:
            events = []

    if not anns:
        anns = [
            {"body": "🚀 CodeX 2026 National Hackathon registrations are officially open! Check the Events tab for tracks and prizes.", "created_at": "2026-11-15T10:00:00Z", "pinned": True},
            {"body": "📚 New technical curriculum on LLM Multi-Agent Swarms & FastHTML published to the Learning Hub.", "created_at": "2026-11-14T14:30:00Z", "pinned": False}
        ]

    task_row = lambda t: Div(
        Div(
            Div(t.get("title", ""), cls="text-sm font-semibold text-white"),
            Div(f"#TK-{t.get('code', t.get('id'))}", cls="text-xs text-slate-400 font-mono mt-0.5"),
            cls="flex-1 min-w-0 mr-3"
        ),
        Form(
            btn_ghost("Mark complete", icon("check", "text-xs text-emerald-400"), cls="text-xs py-1 px-3"),
            method="post", action=f"/tasks/{t['id']}/done"
        ),
        cls="flex items-center justify-between p-3.5 rounded-xl bg-white/[0.03] hover:bg-white/[0.07] border border-white/[0.04] hover:border-white/[0.1] transition-all"
    )

    view_as = Form(
        Select(
            *[Option(r.replace("_", " ").title(), value=r) for r in RANKS if RANKS[r] < RANKS.get(u["role"], 1) or r == u["role"]],
            name="role", cls="input text-xs py-1.5 px-3 bg-[#0b1120] font-mono border-white/10"
        ),
        btn_ghost("Preview Role", cls="text-xs py-1.5 px-3"),
        method="post", action="/view-as", cls="flex items-center gap-2"
    ) if RANKS.get(u["role"], 1) >= 4 and not session.get("view_as") else ""

    cfg = get_site_config()

    # MNC Corporate Hero Banner
    hero_banner = card(
        Div(
            Div(
                Div(
                    badge(f"{cfg.get('university_name', 'HARI UNIVERSITY').upper()} • {cfg.get('university_status', 'DEEMED TO BE UNIVERSITY').upper()}", "amber"),
                    badge("OFFICIAL TECHNICAL BODY", "primary"),
                    cls="flex flex-wrap items-center gap-2 mb-3"
                ),
                H1(f"Welcome back, {u['name']}", cls="font-heading font-extrabold text-3xl sm:text-4xl text-white mb-2 leading-tight tracking-tight"),
                P(cfg.get("site_tagline", "Code • Innovate • Secure • Transform"), cls="text-xs font-mono text-amber-400 font-bold tracking-widest uppercase mb-3"),
                P(
                    cfg.get("hero_subtext", "Empowering next-generation engineers, researchers, and builders at Hari University through high-impact technical development, competitive hackathons, and enterprise-grade engineering tracks."),
                    cls="text-sm text-slate-300 leading-relaxed max-w-2xl"
                ),
                cls="flex-1"
            ),
            Div(
                Img(src="/logo-full.png", alt="Technoverse Club Logo", cls="w-48 sm:w-56 bg-white p-3 rounded-2xl shadow-2xl shrink-0 hidden lg:block"),
                cls="shrink-0"
            ),
            cls="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 relative z-10"
        ),
        cls="bg-gradient-to-br from-[#0f172a]/90 via-[#0b1329]/90 to-[#080c14]/90 border border-blue-500/25 p-6 sm:p-8 mb-8 shadow-2xl relative overflow-hidden"
    )

    # Executive Role-Specific Action Banners
    exec_banner = ""
    if u["role"] == "president":
        exec_banner = card(
            Div(
                Div(
                    Span("PRESIDENTIAL EXECUTIVE DESK", cls="text-[11px] font-mono font-bold tracking-wider text-amber-400 uppercase bg-amber-500/10 border border-amber-500/30 px-3 py-1 rounded-full inline-block mb-2"),
                    H2("Presidential Governance & Mandates", cls="text-xl font-heading font-bold text-white"),
                    P("You are authenticated with supreme constitutional authority over Technoverse Club. Issue executive decrees, grant financial sanctions, or manage website content via Admin Control.", cls="text-xs text-slate-300 mt-1 max-w-2xl"),
                    cls="flex-1"
                ),
                Div(
                    A(btn_primary(icon("gavel", "text-sm mr-1.5"), "Presidential Desk", cls="py-2.5 px-3.5 text-xs font-semibold"), href="/president"),
                    A(btn_danger(icon("admin_panel_settings", "text-sm mr-1.5"), "Admin Control", cls="py-2.5 px-3.5 text-xs font-semibold"), href="/admin-control"),
                    A(btn_primary(icon("military_tech", "text-sm mr-1.5"), "VP Operations", cls="py-2.5 px-3.5 text-xs font-semibold bg-cyan-600 hover:bg-cyan-500"), href="/vice-president"),
                    A(btn_ghost(icon("person_add", "text-sm mr-1.5"), "Provision Members", cls="py-2.5 px-3.5 text-xs font-semibold"), href="/team"),
                    cls="flex flex-wrap items-center gap-2 mt-3 sm:mt-0"
                ),
                cls="flex flex-col sm:flex-row sm:items-center justify-between gap-4"
            ),
            cls="mb-8 border border-amber-500/30 bg-gradient-to-r from-amber-950/30 via-slate-900/60 to-slate-900/40 p-5 shadow-xl"
        )
    elif u["role"] == "vice_president":
        exec_banner = card(
            Div(
                Div(
                    Span("VICE-PRESIDENTIAL OPERATIONS COMMAND", cls="text-[11px] font-mono font-bold tracking-wider text-cyan-400 uppercase bg-cyan-500/10 border border-cyan-500/30 px-3 py-1 rounded-full inline-block mb-2"),
                    H2("VP Operations & Task Allocation", cls="text-xl font-heading font-bold text-white"),
                    P("You are authenticated with executive deputy authority. Dispatch inter-wing operational directives, manage Hari University venue permits, and resolve escalated committee items.", cls="text-xs text-slate-300 mt-1 max-w-2xl"),
                    cls="flex-1"
                ),
                Div(
                    A(btn_primary(icon("military_tech", "text-sm mr-1.5"), "Open VP Operations Command", cls="py-2.5 px-4 text-xs font-semibold bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500"), href="/vice-president"),
                    A(btn_ghost(icon("domain_verification", "text-sm mr-1.5"), "Campus Venue Clearances", cls="py-2.5 px-4 text-xs font-semibold"), href="/vice-president"),
                    cls="flex flex-wrap items-center gap-2.5 mt-3 sm:mt-0"
                ),
                cls="flex flex-col sm:flex-row sm:items-center justify-between gap-4"
            ),
            cls="mb-8 border border-cyan-500/30 bg-gradient-to-r from-cyan-950/30 via-slate-900/60 to-slate-900/40 p-5 shadow-xl"
        )
    elif u["role"] == "club_coordinator":
        exec_banner = card(
            Div(
                Div(
                    Span("SUPERVISORY FACULTY OVERSIGHT", cls="text-[11px] font-mono font-bold tracking-wider text-amber-400 uppercase bg-amber-500/10 border border-amber-500/30 px-3 py-1 rounded-full inline-block mb-2"),
                    H2("Club Coordinator Master Console", cls="text-xl font-heading font-bold text-white"),
                    P("Supervisory faculty authority over the Technoverse Club executive committee, presidential governance, and autonomous CMS administration.", cls="text-xs text-slate-300 mt-1 max-w-2xl"),
                    cls="flex-1"
                ),
                Div(
                    A(btn_primary(icon("gavel", "text-sm mr-1.5"), "Presidential Desk", cls="py-2 px-3 text-xs"), href="/president"),
                    A(btn_danger(icon("admin_panel_settings", "text-sm mr-1.5"), "Admin Control", cls="py-2 px-3 text-xs"), href="/admin-control"),
                    A(btn_primary(icon("military_tech", "text-sm mr-1.5"), "VP Operations", cls="py-2 px-3 text-xs bg-cyan-600 hover:bg-cyan-500"), href="/vice-president"),
                    A(btn_ghost(icon("person_add", "text-sm mr-1.5"), "Provision Members", cls="py-2 px-3 text-xs"), href="/team"),
                    cls="flex flex-wrap items-center gap-2 mt-3 sm:mt-0"
                ),
                cls="flex flex-col sm:flex-row sm:items-center justify-between gap-4"
            ),
            cls="mb-8 border border-amber-500/30 bg-gradient-to-r from-indigo-950/30 via-slate-900/60 to-slate-900/40 p-5 shadow-xl"
        )

    # Core Pillars Section (Dynamic from Site Config)
    pillars = Div(
        card(
            Div(icon("code", "text-blue-400 text-2xl mb-3")),
            H4(cfg.get("pillar1_title", "Software & Systems"), cls="font-heading font-bold text-base mb-1.5 text-white"),
            P(cfg.get("pillar1_desc", "Building scalable full-stack applications, open-source utilities, and developer tooling."), cls="text-xs text-slate-400 leading-relaxed"),
            p="p-5"
        ),
        card(
            Div(icon("smart_toy", "text-amber-400 text-2xl mb-3")),
            H4(cfg.get("pillar2_title", "AI & Machine Learning"), cls="font-heading font-bold text-base mb-1.5 text-white"),
            P(cfg.get("pillar2_desc", "Autonomous agentic swarms, fine-tuned neural models, and enterprise RAG pipelines."), cls="text-xs text-slate-400 leading-relaxed"),
            p="p-5"
        ),
        card(
            Div(icon("security", "text-emerald-400 text-2xl mb-3")),
            H4(cfg.get("pillar3_title", "Cyber Defense & CTF"), cls="font-heading font-bold text-base mb-1.5 text-white"),
            P(cfg.get("pillar3_desc", "Offensive security research, ethical penetration testing, and national security challenges."), cls="text-xs text-slate-400 leading-relaxed"),
            p="p-5"
        ),
        card(
            Div(icon("cloud", "text-cyan-400 text-2xl mb-3")),
            H4(cfg.get("pillar4_title", "Cloud & Infrastructure"), cls="font-heading font-bold text-base mb-1.5 text-white"),
            P(cfg.get("pillar4_desc", "Microservices, containerization, distributed databases, and high-availability operations."), cls="text-xs text-slate-400 leading-relaxed"),
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
                Span(start_date, cls="text-xs font-mono text-slate-400"),
                cls="flex items-center justify-between mb-2"
            ),
            H4(ev.get("title", "Flagship Event"), cls="font-semibold text-sm mb-1 text-white"),
            P(ev.get("description", "") or "Join the campus technical challenge.", cls="text-xs text-slate-400 line-clamp-2 mb-3"),
            Div(
                Span(f"📍 {ev.get('venue') or 'Campus Auditorium'}", cls="text-[11px] text-slate-400 truncate"),
                A("View Details →", href="/events", cls="text-xs font-bold text-blue-400 hover:text-blue-300 ml-auto"),
                cls="flex items-center justify-between pt-2 border-t border-white/[0.05]"
            ),
            cls="p-4 rounded-xl bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.05] transition-all"
        )

    events_section = card(
        Div(
            H3("Upcoming Flagship Summits", cls="font-heading font-bold text-lg text-white"),
            A("Browse All Events →", href="/events", cls="text-xs text-blue-400 hover:text-blue-300 font-mono"),
            cls="flex items-center justify-between mb-4"
        ),
        Div(
            *[event_snippet(e) for e in events] or [P("No upcoming events scheduled.", cls="text-slate-400 text-sm py-4 text-center")],
            cls="grid grid-cols-1 md:grid-cols-3 gap-4"
        ),
        cls="mb-8"
    )

    # Announcements Card
    announcements_card = card(
        Div(
            H3("Official Announcements", cls="font-heading font-bold text-lg text-white"),
            icon("campaign", "text-amber-400 text-xl"),
            cls="flex items-center justify-between mb-4"
        ),
        Div(
            *[Div(
                P(a.get("body", ""), cls="text-sm text-slate-300 leading-relaxed"),
                Div(
                    badge("PINNED", "amber") if a.get("pinned") else "",
                    Span(f"Date: {(a.get('created_at') or '')[:10]}", cls="text-[10px] text-slate-400 font-mono"),
                    cls="flex items-center justify-between mt-2 pt-2 border-t border-white/[0.05]"
                ),
                cls="p-3.5 rounded-xl bg-white/[0.03] border border-white/[0.04] mb-3"
            ) for a in anns],
            cls="space-y-1"
        )
    )

    # My Tasks Card
    my_tasks_card = card(
        Div(
            H3("My Open Deliverables", cls="font-heading font-bold text-lg text-white"),
            A("Full Kanban Board →", href="/tasks", cls="text-xs text-blue-400 hover:text-blue-300 font-mono"),
            cls="flex items-center justify-between mb-4"
        ),
        Div(
            *[task_row(t) for t in mine] or [
                Div(
                    icon("check_circle", "text-emerald-400 text-3xl mb-2"),
                    P("All caught up! No pending tasks assigned to you.", cls="text-sm text-slate-300 font-medium"),
                    cls="text-center py-8 bg-white/[0.02] border border-white/[0.04] rounded-xl"
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
        H3("Executive Navigation Hub", cls="font-heading font-bold text-lg mb-4 text-white"),
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
        exec_banner,
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
    invalidate_cache("dashboard_")
    invalidate_cache("tasks_")
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
