from datetime import datetime, timezone
from fasthtml.common import *
from core import rt, current_user, go, supabase
from components import *
from auth import RANKS, can, log_activity
from cache import get_cached, set_cached, invalidate_cache

FLAGSHIPS = ["none", "CodeX", "AI Nexus", "CyberShield", "DataVerse"]
CATEGORIES = ["Technical", "Workshop", "Hackathon", "Seminar", "Meetup", "Cultural"]

@rt("/events", methods=["GET"])
def events_get(session, flagship: str = "all", category: str = "all", edit_id: int = None):
    u = current_user(session)
    if not u:
        return go("/login")
    role = session.get("view_as") or u["role"]
    rank = RANKS.get(role, 1)

    # Fetch events (cached 20s)
    events = get_cached("events_list", ttl=20)
    if events is None:
        try:
            events = supabase.table("events").select("*, creator:created_by(name)").order("starts_at", desc=False).execute().data or []
            set_cached("events_list", events)
        except Exception as e:
            print("Events fetch error:", e)
            events = []

    # Get my registrations
    try:
        regs = supabase.table("event_registrations").select("event_id, status").eq("member_id", u["id"]).execute().data or []
        my_reg_map = {r["event_id"]: r["status"] for r in regs}
    except Exception:
        my_reg_map = {}

    # Get registration counts per event (cached 20s)
    reg_counts = get_cached("events_reg_counts", ttl=20)
    if reg_counts is None:
        try:
            all_regs = supabase.table("event_registrations").select("event_id").execute().data or []
            reg_counts = {}
            for r in all_regs:
                eid = r["event_id"]
                reg_counts[eid] = reg_counts.get(eid, 0) + 1
            set_cached("events_reg_counts", reg_counts)
        except Exception:
            reg_counts = {}

    # Event to edit
    event_to_edit = None
    if edit_id:
        for ev in events:
            if str(ev.get("id")) == str(edit_id):
                event_to_edit = ev
                break

    # Filters
    filtered_events = events
    if flagship != "all":
        filtered_events = [e for e in filtered_events if e.get("flagship") == flagship]
    if category != "all":
        filtered_events = [e for e in filtered_events if e.get("category") == category]

    def event_card(e):
        eid = e["id"]
        is_registered = eid in my_reg_map
        count = reg_counts.get(eid, 0)
        quota = e.get("quota") or 0
        is_full = quota > 0 and count >= quota
        start_str = (e.get("starts_at") or "")[:16].replace("T", " ")
        creator_name = e.get("creator", {}).get("name") if e.get("creator") else "Technoverse"

        flagship_badge = badge(e.get("flagship"), "amber") if e.get("flagship") and e.get("flagship") != "none" else ""
        can_manage = (role == "event_coordinator" or rank >= 4) and not session.get("view_as")

        reg_button = Form(
            btn_primary(
                icon("check_circle", "text-sm"), "Registered",
                disabled=True,
                cls="opacity-80 bg-emerald-600 hover:bg-emerald-600"
            ) if is_registered else (
                btn_ghost(
                    icon("how_to_reg", "text-sm"), "Join Waitlist" if is_full else "Register Now",
                    type="submit"
                )
            ),
            method="post",
            action=f"/events/{eid}/register"
        ) if not session.get("view_as") else ""

        edit_btn = A(
            btn_ghost(icon("edit", "text-secondary text-xs"), type="button", cls="p-1 hover:bg-white/10 hover:text-white border-0"),
            href=f"/events/{eid}/edit",
            title="Edit Event"
        ) if can_manage else ""

        delete_btn = Form(
            btn_ghost(icon("delete", "text-red-400 text-xs"), type="submit", cls="p-1 hover:bg-red-500/10 border-0"),
            method="post",
            action=f"/events/{eid}/delete",
            onsubmit="return confirm('Delete this event permanently?');",
            title="Delete Event"
        ) if can_manage else ""

        manage_link = A(
            btn_ghost("Manage Event", icon("arrow_forward", "text-sm"), cls="text-xs"),
            href=f"/events/{eid}"
        ) if can_manage else ""

        return card(
            Div(
                Div(
                    badge(e.get("category", "Event"), "primary"),
                    flagship_badge,
                    cls="flex items-center gap-2"
                ),
                Div(
                    edit_btn,
                    delete_btn,
                    Div(
                        icon("groups", "text-muted text-sm ml-2"),
                        Span(f"{count}/{quota if quota else '∞'}", cls="font-mono text-xs text-muted font-bold"),
                        cls="flex items-center gap-1"
                    ),
                    cls="flex items-center"
                ),
                cls="flex items-center justify-between mb-3"
            ),
            H3(e.get("title", ""), cls="font-heading font-bold text-lg mb-2"),
            P(e.get("description", ""), cls="text-xs text-secondary mb-4 line-clamp-3") if e.get("description") else "",
            Div(
                Div(icon("schedule", "text-xs text-muted mr-1"), Span(start_str, cls="font-mono text-xs text-muted"), cls="flex items-center mb-1"),
                Div(icon("location_on", "text-xs text-muted mr-1"), Span(e.get("venue") or "Online / Main Auditorium", cls="text-xs text-muted"), cls="flex items-center"),
                cls="mb-4 pt-3 border-t border-white/5"
            ),
            Div(
                reg_button,
                manage_link,
                cls="flex items-center justify-between pt-2"
            ),
            p="p-5",
            cls="hover:border-primary/40 transition-all flex flex-col justify-between"
        )

    # 1. New Event Modal
    modal = Div(
        Div(onclick="document.getElementById('event-modal').classList.add('hidden')", cls="absolute inset-0 bg-black/60 backdrop-blur-sm"),
        card(
            Div(
                H3("Schedule New Event", cls="font-heading font-bold text-xl"),
                Button(icon("close"), onclick="document.getElementById('event-modal').classList.add('hidden')", type="button", cls="text-muted hover:text-white bg-transparent border-0 cursor-pointer"),
                cls="flex items-center justify-between mb-4"
            ),
            Form(
                input_field("Event Title", "title", placeholder="e.g. CodeX Hackathon 2026", required=True),
                Div(
                    select_field("Category", "category", [(c, c) for c in CATEGORIES]),
                    select_field("Flagship Series", "flagship", [(f, f) for f in FLAGSHIPS]),
                    cls="grid grid-cols-2 gap-3"
                ),
                Div(
                    input_field("Starts At", "starts_at", type="datetime-local", required=True),
                    input_field("Ends At", "ends_at", type="datetime-local", required=True),
                    cls="grid grid-cols-2 gap-3"
                ),
                Div(
                    input_field("Venue / Room", "venue", placeholder="e.g. Lab 4 / Audi-2", required=True),
                    input_field("Capacity Quota (0 for unlimited)", "quota", type="number", value="100"),
                    cls="grid grid-cols-2 gap-3"
                ),
                textarea_field("Description", "description", placeholder="Event agenda, requirements, and benefits...", rows=3),
                Div(
                    btn_ghost("Cancel", type="button", onclick="document.getElementById('event-modal').classList.add('hidden')"),
                    btn_primary("Create Event", type="submit", loading_text="Creating Event..."),
                    cls="flex justify-end gap-3 mt-6"
                ),
                method="post",
                action="/events/new"
            ),
            cls="relative z-10 w-full max-w-xl mx-auto mt-12 max-h-[90vh] overflow-y-auto"
        ),
        id="event-modal",
        cls="fixed inset-0 z-50 flex items-center justify-center p-4 hidden"
    )

    # 2. Edit Event Modal
    edit_modal = ""
    if event_to_edit:
        ev_start = (event_to_edit.get("starts_at") or "")[:16]
        ev_end = (event_to_edit.get("ends_at") or "")[:16]
        edit_modal = Div(
            A(cls="absolute inset-0 bg-black/60 backdrop-blur-sm", href="/events"),
            card(
                Div(
                    H3(f"Edit Event: {event_to_edit.get('title')}", cls="font-heading font-bold text-xl"),
                    A(icon("close"), href="/events", cls="text-muted hover:text-white"),
                    cls="flex items-center justify-between mb-4"
                ),
                Form(
                    input_field("Event Title", "title", value=event_to_edit.get("title", ""), required=True),
                    Div(
                        select_field("Category", "category", [(c, c) for c in CATEGORIES], selected=event_to_edit.get("category")),
                        select_field("Flagship Series", "flagship", [(f, f) for f in FLAGSHIPS], selected=event_to_edit.get("flagship", "none")),
                        cls="grid grid-cols-2 gap-3"
                    ),
                    Div(
                        input_field("Starts At", "starts_at", type="datetime-local", value=ev_start, required=True),
                        input_field("Ends At", "ends_at", type="datetime-local", value=ev_end, required=True),
                        cls="grid grid-cols-2 gap-3"
                    ),
                    Div(
                        input_field("Venue / Room", "venue", value=event_to_edit.get("venue", ""), required=True),
                        input_field("Capacity Quota", "quota", type="number", value=event_to_edit.get("quota", 0)),
                        cls="grid grid-cols-2 gap-3"
                    ),
                    textarea_field("Description", "description", value=event_to_edit.get("description", "") or "", rows=3),
                    Div(
                        A(btn_ghost("Cancel", type="button"), href="/events"),
                        btn_primary("Save Changes", type="submit", loading_text="Saving Changes..."),
                        cls="flex justify-end gap-3 mt-6"
                    ),
                    method="post",
                    action=f"/events/{event_to_edit['id']}/edit"
                ),
                cls="relative z-10 w-full max-w-xl mx-auto mt-12 max-h-[90vh] overflow-y-auto"
            ),
            id="edit-event-modal",
            cls="fixed inset-0 z-50 flex items-center justify-center p-4"
        )

    header = Div(
        Div(
            H1("Events & Operations", cls="font-heading font-bold text-2xl"),
            P("Explore upcoming club meetups, flagship tech summits, and workshops", cls="text-sm text-secondary"),
            cls="flex-1"
        ),
        Div(
            btn_primary(
                icon("add", "text-sm"), "Schedule Event",
                onclick="document.getElementById('event-modal').classList.remove('hidden')",
                type="button"
            ) if (role == "event_coordinator" or rank >= 4) and not session.get("view_as") else "",
            cls="flex items-center gap-3"
        ),
        cls="flex flex-wrap items-center justify-between gap-4 mb-6"
    )

    filter_chips = card(
        Div(
            Div(
                A("All Series", href="/events?flagship=all", cls=f"px-3 py-1.5 rounded-lg text-xs font-mono font-medium {'bg-primary text-white' if flagship == 'all' else 'text-muted hover:bg-white/5'}"),
                *[A(f, href=f"/events?flagship={f}", cls=f"px-3 py-1.5 rounded-lg text-xs font-mono font-medium {'bg-amber text-dark font-bold' if flagship == f else 'text-muted hover:bg-white/5'}") for f in FLAGSHIPS if f != "none"],
                cls="flex items-center gap-1 overflow-x-auto pb-1"
            ),
            cls="flex items-center justify-between"
        ),
        p="p-3 mb-6"
    )

    grid = Div(
        *[event_card(e) for e in filtered_events] or [
            Div(P("No events scheduled matching this filter.", cls="text-muted text-sm text-center py-12"), cls="col-span-full")
        ],
        cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
    )

    return page(session, u, "Events", header, filter_chips, grid, modal, edit_modal)

@rt("/events/{eid}/edit", methods=["GET"])
def event_edit_get(session, eid: int):
    return events_get(session, edit_id=eid)

@rt("/events/{eid}/edit", methods=["POST"])
def event_edit_post(session, eid: int, title: str, category: str, flagship: str, starts_at: str, ends_at: str, venue: str = "", quota: int = 0, description: str = ""):
    u = current_user(session)
    if not u or session.get("view_as"):
        return go("/login")
    if u["role"] != "event_coordinator" and RANKS.get(u["role"], 1) < 4:
        return go("/events")

    payload = {
        "title": title.strip(),
        "category": category,
        "flagship": flagship,
        "starts_at": f"{starts_at}:00Z" if len(starts_at) == 16 else starts_at,
        "ends_at": f"{ends_at}:00Z" if len(ends_at) == 16 else ends_at,
        "venue": venue.strip(),
        "quota": int(quota or 0),
        "description": description.strip() if description else None
    }

    try:
        res = supabase.table("events").update(payload).eq("id", eid).execute()
        invalidate_cache("events_")
        invalidate_cache("dashboard_")
        if res.data:
            log_activity(session, "event_edited", "events", eid, f"Updated event: {title.strip()}")
    except Exception as e:
        print("Event update error:", e)

    return go("/events")

@rt("/events/{eid}/delete", methods=["POST"])
def event_delete_post(session, eid: int):
    u = current_user(session)
    if not u or session.get("view_as"):
        return go("/login")
    if u["role"] != "event_coordinator" and RANKS.get(u["role"], 1) < 4:
        return go("/events")

    try:
        supabase.table("events").delete().eq("id", eid).execute()
        invalidate_cache("events_")
        invalidate_cache("dashboard_")
        log_activity(session, "event_deleted", "events", eid, f"Deleted event #{eid}")
    except Exception as e:
        print("Event delete error:", e)

    return go("/events")

@rt("/events/new", methods=["POST"])
def events_new_post(session, title: str, category: str, flagship: str, starts_at: str, ends_at: str, venue: str = "", quota: int = 0, description: str = ""):
    u = current_user(session)
    if not u or session.get("view_as"):
        return go("/login")
    if u["role"] != "event_coordinator" and RANKS.get(u["role"], 1) < 4:
        return go("/events")

    payload = {
        "title": title.strip(),
        "category": category,
        "flagship": flagship,
        "starts_at": f"{starts_at}:00Z" if len(starts_at) == 16 else starts_at,
        "ends_at": f"{ends_at}:00Z" if len(ends_at) == 16 else ends_at,
        "venue": venue.strip(),
        "quota": int(quota or 0),
        "description": description.strip() if description else None,
        "created_by": u["id"]
    }

    try:
        res = supabase.table("events").insert(payload).execute()
        invalidate_cache("events_")
        invalidate_cache("dashboard_")
        if res.data:
            log_activity(session, "event_created", "events", res.data[0]["id"], f"Scheduled event: {title.strip()}")
    except Exception as e:
        print("Event creation error:", e)

    return go("/events")

@rt("/events/{eid}/register", methods=["POST"])
def events_register(session, eid: int):
    u = current_user(session)
    if not u or session.get("view_as"):
        return go("/login")

    try:
        ev = supabase.table("events").select("quota").eq("id", eid).single().execute().data
        quota = ev.get("quota", 0) if ev else 0
        count = supabase.table("event_registrations").select("id", count="exact").eq("event_id", eid).execute().count or 0

        status = "waitlist" if (quota > 0 and count >= quota) else "registered"
        supabase.table("event_registrations").upsert({
            "event_id": eid,
            "member_id": u["id"],
            "status": status
        }).execute()
        invalidate_cache("events_")
        log_activity(session, f"event_{status}", "events", eid, f"Registered for event ({status})")
    except Exception as e:
        print("Registration error:", e)

    return go("/events")

@rt("/events/{eid}", methods=["GET"])
def event_detail(session, eid: int):
    u = current_user(session)
    if not u:
        return go("/login")
    role = session.get("view_as") or u["role"]
    rank = RANKS.get(role, 1)

    try:
        ev = supabase.table("events").select("*").eq("id", eid).single().execute().data
    except Exception:
        ev = None

    if not ev:
        return go("/events")

    # Registered members
    try:
        regs = supabase.table("event_registrations").select("status, created_at, member:member_id(id, name, roll, email, branch)").eq("event_id", eid).execute().data or []
    except Exception:
        regs = []

    # Attendance
    try:
        att_rows = supabase.table("attendance").select("member_id, present").eq("event_id", eid).execute().data or []
        att_map = {a["member_id"]: a["present"] for a in att_rows}
    except Exception:
        att_map = {}

    present_count = sum(1 for p in att_map.values() if p)

    header = Div(
        A(icon("arrow_back", "text-sm mr-1"), "Back to Events", href="/events", cls="text-secondary hover:text-white text-xs font-mono inline-flex items-center mb-3"),
        Div(
            Div(
                H1(ev["title"], cls="font-heading font-bold text-2xl"),
                P(f"Category: {ev['category']} • Venue: {ev.get('venue', 'N/A')}", cls="text-sm text-secondary mt-1"),
                cls="flex-1"
            ),
            badge(ev.get("flagship", "Standard"), "amber" if ev.get("flagship") != "none" else "secondary"),
            cls="flex flex-wrap items-center justify-between gap-4"
        ),
        cls="mb-6"
    )

    stats = Div(
        stat_card("Total Registered", len(regs), "groups"),
        stat_card("Confirmed Present", present_count, "check_circle"),
        stat_card("Capacity Quota", ev.get("quota") or "Unlimited", "meeting_room"),
        cls="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6"
    )

    def attendee_row(r):
        m = r.get("member") or {}
        mid = m.get("id")
        is_pres = att_map.get(mid, False)
        
        toggle_btn = Form(
            Input(type="hidden", name="mid", value=mid),
            Input(type="hidden", name="present", value="false" if is_pres else "true"),
            btn_success("Present", icon("check", "text-xs"), cls="text-xs py-1 px-3") if is_pres else btn_ghost("Mark Present", cls="text-xs py-1 px-3"),
            method="post",
            action=f"/events/{eid}/attendance"
        ) if can(role, "events", "attendance") and not session.get("view_as") else (
            badge("Present" if is_pres else "Absent", "done" if is_pres else "secondary")
        )

        return Div(
            Div(
                avatar(m.get("name", "?"), cls="w-8 h-8"),
                Div(
                    Div(m.get("name", "Unknown"), cls="text-sm font-semibold"),
                    Div(f"{m.get('roll', '')} • {m.get('branch', 'Core')}", cls="text-xs text-muted font-mono"),
                    cls="truncate"
                ),
                cls="flex items-center gap-3"
            ),
            Div(
                badge(r.get("status", "registered").upper(), r.get("status", "registered")),
                toggle_btn,
                cls="flex items-center gap-3"
            ),
            cls="flex items-center justify-between p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors"
        )

    attendees_card = card(
        H3("Attendee List & Attendance Marking", cls="font-heading font-semibold text-lg mb-4"),
        Div(
            *[attendee_row(r) for r in regs] or [P("No registrations for this event yet.", cls="text-muted text-sm py-4 text-center")],
            cls="space-y-2"
        )
    )

    return page(session, u, f"{ev['title']} | Operations", header, stats, attendees_card)

@rt("/events/{eid}/attendance", methods=["POST"])
def event_mark_attendance(session, eid: int, mid: str, present: str):
    u = current_user(session)
    if not u or session.get("view_as"):
        return go("/login")
    if u["role"] != "event_coordinator" and RANKS.get(u["role"], 1) < 4:
        return go(f"/events/{eid}")

    is_p = (present.lower() == "true")
    try:
        supabase.table("attendance").upsert({
            "event_id": eid,
            "member_id": mid,
            "present": is_p,
            "marked_by": u["id"]
        }).execute()
        log_activity(session, "attendance_marked", "events", eid, f"Marked {'present' if is_p else 'absent'} for member {mid}")
    except Exception as e:
        print("Attendance error:", e)

    return go(f"/events/{eid}")
