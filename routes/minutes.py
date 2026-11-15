from fasthtml.common import *
from core import rt, current_user, go, supabase
from components import *
from auth import RANKS, can, log_activity

@rt("/minutes", methods=["GET"])
def minutes_get(session):
    u = current_user(session)
    if not u:
        return go("/login")
    role = session.get("view_as") or u["role"]
    rank = RANKS.get(role, 1)

    if rank < 3 and role != "secretary":
        return page(session, u, "Meeting Minutes", card(H2("Access Restricted", cls="font-heading font-bold text-xl text-red-400 mb-2"), P("Meeting Minutes are reserved for Secretary, Leads, and Executive Board members.", cls="text-sm text-secondary")))

    try:
        sessions = supabase.table("minutes").select("*, creator:created_by(name)").order("held_at", desc=True).execute().data or []
    except Exception:
        sessions = []

    try:
        actions = supabase.table("action_items").select("*").execute().data or []
    except Exception:
        actions = []

    actions_by_mid = {}
    for a in actions:
        mid = a["minutes_id"]
        actions_by_mid.setdefault(mid, []).append(a)

    can_create = (role == "secretary" or rank >= 4) and not session.get("view_as")

    header = Div(
        Div(
            H1("Meeting Minutes", cls="font-heading font-bold text-2xl"),
            P("Official records of core executive sessions, action items, and task conversions", cls="text-sm text-secondary"),
            cls="flex-1"
        ),
        Div(
            btn_primary(
                icon("add_circle", "text-sm"), "Record Meeting",
                onclick="document.getElementById('minutes-modal').classList.remove('hidden')",
                type="button"
            ) if can_create else "",
            cls="flex items-center gap-3"
        ),
        cls="flex flex-wrap items-center justify-between gap-4 mb-6"
    )

    def session_card(m):
        mid = m["id"]
        m_actions = actions_by_mid.get(mid, [])
        held_date = (m.get("held_at") or "")[:10]
        creator = m.get("creator", {}).get("name") if m.get("creator") else "Secretary"

        convert_btn = Form(
            btn_ghost(icon("sync_alt", "text-xs"), "Convert to Tasks", type="submit", cls="text-xs py-1 px-3"),
            method="post",
            action=f"/minutes/{mid}/convert",
            cls="inline-block"
        ) if m_actions and can_create else ""

        return card(
            Div(
                Div(
                    H3(m.get("title", "Core Executive Meeting"), cls="font-heading font-bold text-lg"),
                    P(f"Held on {held_date} • Recorded by {creator}", cls="text-xs text-muted font-mono mt-0.5"),
                    cls="flex-1"
                ),
                convert_btn,
                cls="flex items-center justify-between mb-3"
            ),
            P(m.get("summary", ""), cls="text-sm text-secondary mb-4 leading-relaxed") if m.get("summary") else "",
            Div(
                H4("Action Items", cls="text-xs font-mono text-muted uppercase tracking-wider mb-2 font-bold"),
                Div(
                    *[Div(
                        icon("check_box_outline_blank", "text-xs text-primary mt-0.5 shrink-0"),
                        Span(act.get("text", ""), cls="text-xs text-secondary leading-normal"),
                        cls="flex items-start gap-2 p-2 rounded-lg bg-white/5"
                    ) for act in m_actions] or [P("No pending action items recorded.", cls="text-xs text-muted italic")],
                    cls="space-y-1.5"
                ),
                cls="pt-3 border-t border-white/5"
            ),
            cls="mb-4",
            p="p-5"
        )

    modal = Div(
        Div(onclick="document.getElementById('minutes-modal').classList.add('hidden')", cls="absolute inset-0 bg-black/60 backdrop-blur-sm"),
        card(
            Div(
                H3("Record Meeting Minutes", cls="font-heading font-bold text-xl"),
                Button(icon("close"), onclick="document.getElementById('minutes-modal').classList.add('hidden')", type="button", cls="text-muted hover:text-white bg-transparent border-0 cursor-pointer"),
                cls="flex items-center justify-between mb-4"
            ),
            Form(
                input_field("Meeting Title", "title", placeholder="e.g. Weekly Executive Review #12", required=True),
                input_field("Date Held", "held_at", type="date", required=True),
                textarea_field("Executive Summary & Key Decisions", "summary", placeholder="Document key discussions, approvals, and outcomes...", rows=4, required=True),
                textarea_field("Action Items (One per line)", "action_items", placeholder="e.g.\nDraft Hackathon Rulebook\nContact Audio Vendor for Audi-2\nConfirm Guest Speaker Schedule", rows=3),
                Div(
                    btn_ghost("Cancel", type="button", onclick="document.getElementById('minutes-modal').classList.add('hidden')"),
                    btn_primary("Save Minutes", type="submit"),
                    cls="flex justify-end gap-3 mt-6"
                ),
                method="post",
                action="/minutes/new"
            ),
            cls="relative z-10 w-full max-w-xl mx-auto mt-12 max-h-[90vh] overflow-y-auto"
        ),
        id="minutes-modal",
        cls="fixed inset-0 z-50 flex items-center justify-center p-4 hidden"
    )

    list_container = Div(
        *[session_card(m) for m in sessions] or [
            Div(P("No meeting minutes recorded yet.", cls="text-muted text-sm text-center py-12"), cls="col-span-full")
        ],
        cls="space-y-4"
    )

    return page(session, u, "Meeting Minutes", header, list_container, modal)

@rt("/minutes/new", methods=["POST"])
def minutes_new_post(session, title: str, held_at: str, summary: str, action_items: str = ""):
    u = current_user(session)
    if not u or session.get("view_as"):
        return go("/login")
    if u["role"] != "secretary" and RANKS.get(u["role"], 1) < 4:
        return go("/minutes")

    payload = {
        "title": title.strip(),
        "held_at": f"{held_at}T00:00:00Z" if len(held_at) == 10 else held_at,
        "summary": summary.strip(),
        "created_by": u["id"]
    }

    try:
        res = supabase.table("minutes").insert(payload).execute()
        if res.data:
            mid = res.data[0]["id"]
            log_activity(session, "minutes_created", "minutes", mid, f"Recorded minutes: {title.strip()}")

            # Insert action items
            if action_items:
                lines = [line.strip() for line in action_items.split("\n") if line.strip()]
                for line in lines:
                    supabase.table("action_items").insert({
                        "minutes_id": mid,
                        "text": line
                    }).execute()
    except Exception as e:
        print("Minutes creation error:", e)

    return go("/minutes")

@rt("/minutes/{mid}/convert", methods=["POST"])
def minutes_convert_to_tasks(session, mid: int):
    u = current_user(session)
    if not u or session.get("view_as"):
        return go("/login")
    if u["role"] != "secretary" and RANKS.get(u["role"], 1) < 4:
        return go("/minutes")

    try:
        items = supabase.table("action_items").select("*").eq("minutes_id", mid).is_("task_id", "null").execute().data or []
        converted_count = 0
        for item in items:
            # Create a task from this action item
            task_res = supabase.table("tasks").insert({
                "title": item["text"],
                "description": f"Generated from Meeting Minutes #{mid}",
                "priority": "medium",
                "status": "todo",
                "created_by": u["id"],
                "sprint": "Current Sprint"
            }).execute()
            if task_res.data:
                tid = task_res.data[0]["id"]
                supabase.table("action_items").update({"task_id": tid}).eq("id", item["id"]).execute()
                converted_count += 1
        log_activity(session, "action_items_converted", "minutes", mid, f"Converted {converted_count} action items into Tasks")
    except Exception as e:
        print("Convert to tasks error:", e)

    return go("/minutes")
