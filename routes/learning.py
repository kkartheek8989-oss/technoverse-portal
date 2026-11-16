from fasthtml.common import *
from core import rt, current_user, go, supabase
from components import *
from auth import RANKS, can, log_activity
from cache import get_cached, set_cached, invalidate_cache

TRACKS = ["Web Development", "AI & Machine Learning", "Cyber Security", "Cloud & DevOps", "System Design", "Competitive Programming"]
LEVELS = ["beginner", "intermediate", "advanced"]

@rt("/learning", methods=["GET"])
def learning_get(session, track: str = "all", level: str = "all"):
    u = current_user(session)
    if not u:
        return go("/login")
    role = session.get("view_as") or u["role"]
    rank = RANKS.get(role, 1)

    resources = get_cached("learning_resources", ttl=30)
    if resources is None:
        try:
            resources = supabase.table("resources").select("*, creator:created_by(name)").order("created_at", desc=True).execute().data or []
            set_cached("learning_resources", resources)
        except Exception:
            resources = []

    if track != "all":
        resources = [r for r in resources if r.get("track") == track]
    if level != "all":
        resources = [r for r in resources if r.get("level") == level]

    can_create = (role == "technical_lead" or rank >= 4) and not session.get("view_as")

    header = Div(
        Div(
            H1("Learning Hub", cls="font-heading font-bold text-2xl"),
            P("Curated technical curricula, workshop materials, and documentation tracks", cls="text-sm text-secondary"),
            cls="flex-1"
        ),
        Div(
            btn_primary(
                icon("post_add", "text-sm"), "Add Resource",
                onclick="document.getElementById('resource-modal').classList.remove('hidden')",
                type="button"
            ) if can_create else "",
            cls="flex items-center gap-3"
        ),
        cls="flex flex-wrap items-center justify-between gap-4 mb-6"
    )

    track_chips = card(
        Div(
            A("All Tracks", href="/learning?track=all", cls=f"px-3 py-1.5 rounded-lg text-xs font-mono font-medium {'bg-primary text-white' if track == 'all' else 'text-muted hover:bg-white/5'}"),
            *[A(t, href=f"/learning?track={t}", cls=f"px-3 py-1.5 rounded-lg text-xs font-mono font-medium {'bg-primary text-white' if track == t else 'text-muted hover:bg-white/5'}") for t in TRACKS],
            cls="flex items-center gap-1 overflow-x-auto pb-1"
        ),
        p="p-3 mb-6"
    )

    def resource_card(r):
        lvl = r.get("level", "beginner")
        lvl_variant = {"beginner": "low", "intermediate": "medium", "advanced": "urgent"}.get(lvl, "secondary")
        link = r.get("link_url") or "#"
        creator = r.get("creator", {}).get("name") if r.get("creator") else "Technical Team"

        return card(
            Div(
                badge(r.get("track", "Engineering"), "primary"),
                badge(lvl.upper(), lvl_variant),
                cls="flex items-center justify-between mb-3"
            ),
            H3(r.get("title", "Resource"), cls="font-heading font-bold text-base mb-2"),
            P(r.get("summary", ""), cls="text-xs text-secondary mb-4 line-clamp-3") if r.get("summary") else "",
            Div(
                Span(f"Added by {creator}", cls="text-[11px] text-muted font-mono"),
                A(
                    btn_primary("Access Hub", icon("open_in_new", "text-xs"), cls="text-xs py-1.5 px-3"),
                    href=link,
                    target="_blank" if link.startswith("http") else "_self"
                ),
                cls="flex items-center justify-between pt-3 border-t border-white/5"
            ),
            p="p-5",
            cls="hover:border-primary/40 transition-all flex flex-col justify-between"
        )

    grid = Div(
        *[resource_card(r) for r in resources] or [
            Div(P("No learning resources available for this track yet.", cls="text-muted text-sm text-center py-12"), cls="col-span-full")
        ],
        cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
    )

    modal = Div(
        Div(onclick="document.getElementById('resource-modal').classList.add('hidden')", cls="absolute inset-0 bg-black/60 backdrop-blur-sm"),
        card(
            Div(
                H3("Publish Learning Resource", cls="font-heading font-bold text-xl"),
                Button(icon("close"), onclick="document.getElementById('resource-modal').classList.add('hidden')", type="button", cls="text-muted hover:text-white bg-transparent border-0 cursor-pointer"),
                cls="flex items-center justify-between mb-4"
            ),
            Form(
                input_field("Resource Title", "title", placeholder="e.g. Modern Web Development Bootcamp Guide", required=True),
                Div(
                    select_field("Domain Track", "track", [(t, t) for t in TRACKS]),
                    select_field("Proficiency Level", "level", [(l, l.capitalize()) for l in LEVELS]),
                    cls="grid grid-cols-2 gap-3"
                ),
                input_field("Resource URL / Link", "link_url", placeholder="https://github.com/... or documentation link", required=True),
                textarea_field("Overview & Syllabus", "summary", placeholder="Brief description of skills covered and prerequisites...", rows=3),
                Div(
                    btn_ghost("Cancel", type="button", onclick="document.getElementById('resource-modal').classList.add('hidden')"),
                    btn_primary("Publish to Hub", type="submit", loading_text="Publishing..."),
                    cls="flex justify-end gap-3 mt-6"
                ),
                method="post",
                action="/learning/new"
            ),
            cls="relative z-10 w-full max-w-lg mx-auto mt-16"
        ),
        id="resource-modal",
        cls="fixed inset-0 z-50 flex items-center justify-center p-4 hidden"
    )

    return page(session, u, "Learning Hub", header, track_chips, grid, modal)

@rt("/learning/new", methods=["POST"])
def learning_new_post(session, title: str, track: str, level: str, link_url: str, summary: str = ""):
    u = current_user(session)
    if not u or session.get("view_as"):
        return go("/login")
    if u["role"] != "technical_lead" and RANKS.get(u["role"], 1) < 4:
        return go("/learning")

    payload = {
        "title": title.strip(),
        "track": track,
        "level": level,
        "link_url": link_url.strip(),
        "summary": summary.strip() if summary else None,
        "created_by": u["id"]
    }

    try:
        res = supabase.table("resources").insert(payload).execute()
        invalidate_cache("learning_")
        if res.data:
            log_activity(session, "resource_created", "learning", res.data[0]["id"], f"Added learning resource: {title.strip()}")
    except Exception as e:
        print("Learning resource creation error:", e)

    return go("/learning")
