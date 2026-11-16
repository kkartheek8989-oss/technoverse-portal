import os
from datetime import datetime, timezone
from fasthtml.common import *
from core import rt, current_user, go, supabase
from components import *
from auth import log_activity

# Default campus venue clearances list
CAMPUS_VENUES = [
    {"id": "v1", "venue": "Hari Univ Central Auditorium", "capacity": "800 Seats", "facility": "Keynotes & Tech Summits", "status": "Approved", "permit": "HU-AUD-2026/89"},
    {"id": "v2", "venue": "Advanced Computing & AI Lab", "capacity": "120 Workstations", "facility": "Hands-on Workshops & Hackathons", "status": "Approved", "permit": "HU-LAB-2026/14"},
    {"id": "v3", "venue": "Academic Seminar Hall 204", "capacity": "250 Seats", "facility": "Code Reviews & Guest Lectures", "status": "In Clearance", "permit": "HU-SEM-2026/02"},
    {"id": "v4", "venue": "Open-Air Tech Amphitheatre", "capacity": "1500 Capacity", "facility": "Annual Flagship Tech Expo", "status": "Pending Dean Signoff", "permit": "HU-OAA-2026/91"},
]

@rt("/vice-president", methods=["GET"])
def vice_president_dashboard(session, msg: str = "", error: str = ""):
    user = current_user(session)
    if not user:
        return go("/login")
    if user["role"] not in ["vice_president", "club_coordinator"]:
        return go("/?error=Access+Restricted:+The+VP+Operations+Command+is+exclusively+reserved+for+the+Vice+President.")

    # Fetch recent VP Dispatches from tasks
    try:
        dispatches = supabase.table("tasks").select("*").ilike("title", "%[VP DISPATCH]%").order("created_at", desc=True).limit(6).execute().data or []
    except Exception as e:
        print("Error fetching VP dispatches:", e)
        dispatches = []

    # Fetch leads to whom VP can delegate operational tasks
    try:
        leads = supabase.table("members").select("id, name, roll, role, branch").in_("role", ["technical_lead", "event_coordinator", "secretary", "treasurer"]).execute().data or []
    except Exception as e:
        print("Error fetching leads for VP:", e)
        leads = []

    # Fetch pending action items from minutes
    try:
        action_items = supabase.table("action_items").select("*").limit(6).execute().data or []
    except Exception as e:
        print("Error fetching action items:", e)
        action_items = []

    lead_options = [(m["id"], f"{m['name']} ({m['role'].replace('_', ' ').title()} • {m['branch']})") for m in leads]
    if not lead_options:
        lead_options = [("", "No leads available")]

    return page(
        session, user, "VP Operations Command",
        # Hero Banner
        card(
            Div(
                Div(
                    Div(
                        Span("VICE-PRESIDENTIAL OPERATIONS COMMAND", cls="text-xs font-mono font-bold tracking-wider text-cyan-400 uppercase bg-cyan-500/10 border border-cyan-500/20 px-3 py-1 rounded-full inline-block mb-2"),
                        H1("Operational Execution & Committee Command", cls="text-2xl md:text-3xl font-heading font-bold text-white"),
                        P(f"Active Command: {user['name']} • Official Vice President of Technoverse Club", cls="text-slate-300 text-sm mt-1"),
                        cls="space-y-1"
                    ),
                    Div(
                        A(
                            icon("assignment_turned_in", "text-sm mr-1.5"), "Live Kanban Board",
                            href="/tasks",
                            cls="inline-flex items-center text-xs font-mono font-semibold bg-white/[0.05] hover:bg-white/[0.1] text-cyan-300 border border-cyan-500/30 px-3.5 py-2 rounded-xl transition-all"
                        ),
                        A(
                            icon("event_available", "text-sm mr-1.5"), "Event Schedule",
                            href="/events",
                            cls="inline-flex items-center text-xs font-mono font-semibold bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white shadow-lg shadow-cyan-600/25 px-3.5 py-2 rounded-xl transition-all"
                        ),
                        cls="flex flex-wrap items-center gap-2 mt-4 md:mt-0"
                    ),
                    cls="flex flex-col md:flex-row md:items-center justify-between gap-4"
                ),
                cls="relative z-10"
            ),
            cls="relative overflow-hidden mb-8 border border-cyan-500/20 bg-gradient-to-br from-[#0a1526] via-[#0d1e3d] to-[#081120]"
        ),

        # Alerts
        Div(msg, cls="bg-emerald-900/40 border border-emerald-500/30 p-4 rounded-xl text-emerald-200 text-sm mb-6") if msg else "",
        Div(error, cls="bg-red-900/40 border border-red-500/30 p-4 rounded-xl text-red-200 text-sm mb-6") if error else "",

        # VP Operational Metrics
        Div(
            stat_card("Executive Role", "VICE PRESIDENT", "military_tech", "Executive Deputy & Operations Lead"),
            stat_card("Active Dispatches", len(dispatches), "task", "Operational Directives in Flight"),
            stat_card("Campus Venues", f"{len(CAMPUS_VENUES)} CLEARANCES", "stadium", "Auditoriums & AI Computing Labs"),
            stat_card("Operational Readiness", "98.4%", "speed", "Execution Velocity Index"),
            cls="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
        ),

        # 2-Column Command Grid
        Div(
            # Left: Inter-Wing Operational Dispatcher
            Div(
                card(
                    Div(
                        icon("send_and_archive", "text-cyan-400 text-xl"),
                        H2("Inter-Wing Operational Task Dispatch", cls="text-lg font-heading font-bold text-white"),
                        cls="flex items-center gap-2.5 mb-1"
                    ),
                    P("Directly assign high-priority operational tasks to Technical Leads, Event Coordinators, or Secretariat.", cls="text-xs text-slate-400 mb-5"),
                    Form(
                        input_field("Operational Directive Title", "title", placeholder="e.g. Lab 4 Equipment Setup for Python Hackathon"),
                        select_field("Assign to Lead Officer", "assigned_to", lead_options),
                        select_field("Execution Priority", "priority", [
                            ("urgent", "URGENT (24-Hour Turnaround)"),
                            ("high", "HIGH (Sprint Milestone Deliverable)"),
                            ("medium", "MEDIUM (Normal Operational Schedule)")
                        ]),
                        textarea_field("Operational Instructions & Deliverables", "description", placeholder="Specify clear execution steps, required equipment, coordination points, and deliverables..."),
                        btn_primary(icon("rocket_launch", "text-sm mr-1"), "Dispatch Operational Task", type="submit", cls="w-full py-2.5 font-semibold text-sm", loading_text="Dispatching Task..."),
                        method="post",
                        action="/vice-president/dispatch"
                    ),
                    cls="mb-8"
                ),

                # Live Feed of VP Dispatches
                card(
                    Div(
                        icon("checklist_rtl", "text-blue-400 text-xl"),
                        H3("Recent Operational Dispatches", cls="text-base font-heading font-bold text-white"),
                        cls="flex items-center gap-2.5 mb-4"
                    ),
                    Div(
                        *[
                            Div(
                                Div(
                                    Div(
                                        Span(d.get("title", "Operational Task"), cls="text-sm font-semibold text-white block"),
                                        Span(f"Sprint: {d.get('sprint', 'Active')} • Domain: Operations", cls="text-xs text-slate-400 font-mono mt-0.5 block"),
                                        cls="flex-1"
                                    ),
                                    badge(d.get("status", "todo").upper(), "doing" if d.get("status") == "doing" else "todo"),
                                    cls="flex items-start justify-between gap-3"
                                ),
                                P(d.get("description") or "Operational directives dispatched by Vice President.", cls="text-xs text-slate-300 mt-2 bg-white/[0.02] p-2 rounded-lg border border-white/5"),
                                cls="p-3.5 rounded-xl border border-white/[0.06] bg-white/[0.02] mb-3 last:mb-0 hover:bg-white/[0.04] transition-all"
                            ) for d in dispatches
                        ] if dispatches else [
                            Div(
                                P("No recent operational dispatches. All wings executing on schedule.", cls="text-sm text-slate-400 font-mono text-center py-6")
                            )
                        ],
                        cls="space-y-2"
                    )
                )
            ),

            # Right Column: Campus Venue Clearances & Action Items
            Div(
                # Campus Venue Clearances
                card(
                    Div(
                        icon("domain_verification", "text-emerald-400 text-xl"),
                        H2("Campus Event & Venue Clearances", cls="text-lg font-heading font-bold text-white"),
                        cls="flex items-center gap-2.5 mb-1"
                    ),
                    P("Official Hari University facility permits and operational booking clearance tracker.", cls="text-xs text-slate-400 mb-4"),
                    Div(
                        *[
                            Div(
                                Div(
                                    Div(
                                        Span(v["venue"], cls="text-sm font-semibold text-white block"),
                                        Span(f"{v['facility']} • Capacity: {v['capacity']}", cls="text-xs text-slate-400 block mt-0.5"),
                                        Span(f"Permit Ref: {v['permit']}", cls="text-[10px] text-amber-400 font-mono block mt-1"),
                                        cls="flex-1"
                                    ),
                                    badge(v["status"].upper(), "done" if "Approved" in v["status"] else "amber"),
                                    cls="flex items-start justify-between gap-2"
                                ),
                                cls="p-3.5 rounded-xl border border-white/[0.06] bg-white/[0.02] mb-3 last:mb-0"
                            ) for v in CAMPUS_VENUES
                        ],
                        cls="space-y-2"
                    ),
                    cls="mb-8"
                ),

                # Escalated Minutes Action Items
                card(
                    Div(
                        icon("priority_high", "text-amber-400 text-xl"),
                        H2("Escalated Meeting Action Items", cls="text-lg font-heading font-bold text-white"),
                        cls="flex items-center gap-2.5 mb-1"
                    ),
                    P("Action items escalated from general body & committee meetings requiring VP resolution.", cls="text-xs text-slate-400 mb-4"),
                    Div(
                        *[
                            Div(
                                Div(
                                    Span(a.get("item", "Committee Action Item"), cls="text-sm text-white font-medium block"),
                                    Span(f"Assigned: {a.get('assigned_to', 'Committee Lead')}", cls="text-xs text-slate-400 font-mono mt-0.5 block"),
                                    cls="flex-1"
                                ),
                                Form(
                                    Input(type="hidden", name="item_id", value=str(a.get("id"))),
                                    btn_success("Clear Item", type="submit", cls="text-xs py-1 px-2.5"),
                                    method="post",
                                    action="/vice-president/clear-item"
                                ),
                                cls="flex items-center justify-between gap-3 p-3 rounded-xl border border-white/[0.05] bg-white/[0.02] mb-2.5 last:mb-0"
                            ) for a in action_items
                        ] if action_items else [
                            Div(
                                P("No pending action items requiring VP escalation.", cls="text-sm text-slate-400 font-mono text-center py-6")
                            )
                        ]
                    ),
                    A(
                        icon("description", "text-sm mr-1.5"), "Open Full Meeting Minutes",
                        href="/minutes",
                        cls="mt-5 block text-center text-xs font-mono text-cyan-400 hover:text-cyan-300 py-2 border border-cyan-500/20 rounded-xl bg-cyan-500/5 transition-all"
                    )
                )
            ),
            cls="grid grid-cols-1 lg:grid-cols-2 gap-8"
        )
    )

@rt("/vice-president/dispatch", methods=["POST"])
def vp_dispatch_post(session, title: str, assigned_to: str, priority: str, description: str):
    user = current_user(session)
    if not user or user["role"] not in ["vice_president", "club_coordinator"]:
        return go("/login")

    clean_title = (title or "").strip()
    if not clean_title:
        return go("/vice-president?error=Directive+title+is+required.")

    now_iso = datetime.now(timezone.utc).isoformat()

    # Create an actual high-priority task in tasks table
    try:
        supabase.table("tasks").insert({
            "title": f"[VP DISPATCH] {clean_title}",
            "description": description or f"Operational task dispatched by Vice President {user['name']}",
            "status": "todo",
            "priority": priority or "high",
            "sprint": "Active Sprint",
            "assigned_to": assigned_to or None,
            "created_by": user["id"],
            "created_at": now_iso
        }).execute()

        log_activity(session, "vp_dispatch", "tasks", None, f"VP {user['name']} dispatched operational task '{clean_title}'")
    except Exception as e:
        print("Error creating task from VP dispatch:", e)
        return go(f"/vice-president?error=Failed+to+dispatch+task:+{str(e)[:100]}")

    return go(f"/vice-president?msg=Operational+directive+'{clean_title}'+dispatched+to+lead+officer+and+added+to+Kanban.")

@rt("/vice-president/clear-item", methods=["POST"])
def vp_clear_item_post(session, item_id: str):
    user = current_user(session)
    if not user or user["role"] not in ["vice_president", "club_coordinator"]:
        return go("/login")

    try:
        supabase.table("action_items").delete().eq("id", item_id).execute()
        log_activity(session, "clear_action_item", "minutes", item_id, f"VP {user['name']} cleared action item #{item_id}")
    except Exception as e:
        print("Error clearing action item:", e)
        return go(f"/vice-president?error=Failed+to+clear+item:+{str(e)[:100]}")

    return go("/vice-president?msg=Action+item+successfully+resolved+and+marked+cleared.")
