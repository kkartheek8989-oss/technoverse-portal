import csv
import io
from fasthtml.common import *
from core import rt, current_user, go, supabase
from components import *
from auth import RANKS
from cache import get_cached, set_cached

SECTIONS_LIST = ["all", "auth", "tasks", "events", "finance", "minutes", "team", "files", "learning", "join_requests"]

@rt("/activity", methods=["GET"])
def activity_get(session, section: str = "all"):
    u = current_user(session)
    if not u:
        return go("/login")
    role = session.get("view_as") or u["role"]
    rank = RANKS.get(role, 1)

    if rank < 4:
        return page(session, u, "Activity Logs", card(H2("Executive Access Only", cls="font-heading font-bold text-xl text-red-400 mb-2"), P("The permanent audit log is restricted to Executive Board members and the Club Coordinator.", cls="text-sm text-secondary")))

    logs = get_cached(f"activity_logs_{section}", ttl=10)
    if logs is None:
        try:
            q = supabase.table("activity").select("*").order("created_at", desc=True).limit(100)
            if section != "all":
                q = q.eq("section", section)
            logs = q.execute().data or []
            set_cached(f"activity_logs_{section}", logs)
        except Exception:
            logs = []

    header = Div(
        Div(
            H1("Activity Audit Trail", cls="font-heading font-bold text-2xl"),
            P("Immutable organization audit feed tracking all member logins, administrative mutations, and operations", cls="text-sm text-secondary"),
            cls="flex-1"
        ),
        Div(
            A(
                btn_ghost(icon("download", "text-sm"), "Export Audit CSV"),
                href="/activity/export.csv"
            ),
            cls="flex items-center gap-3"
        ),
        cls="flex flex-wrap items-center justify-between gap-4 mb-6"
    )

    filter_chips = card(
        Div(
            A("All Sections", href="/activity?section=all", cls=f"px-3 py-1.5 rounded-lg text-xs font-mono font-medium {'bg-primary text-white' if section == 'all' else 'text-muted hover:bg-white/5'}"),
            *[A(s.capitalize(), href=f"/activity?section={s}", cls=f"px-3 py-1.5 rounded-lg text-xs font-mono font-medium {'bg-primary text-white' if section == s else 'text-muted hover:bg-white/5'}") for s in SECTIONS_LIST if s != "all"],
            cls="flex items-center gap-1 overflow-x-auto pb-1"
        ),
        p="p-3 mb-6"
    )

    def log_row(log):
        created_str = (log.get("created_at") or "")[:19].replace("T", " ")
        mem_name = log.get("member_name") or "System / Anonymous"
        log_role = log.get("role") or "member"
        action_name = (log.get("action") or "action").replace("_", " ").title()

        return Div(
            Div(
                avatar(mem_name, cls="w-8 h-8 text-[10px]"),
                Div(
                    Div(
                        Span(mem_name, cls="font-semibold text-sm"),
                        badge(log_role.upper(), "amber" if log_role == "club_coordinator" else "secondary"),
                        badge(log.get("section", "system").upper(), "primary"),
                        cls="flex items-center gap-2 mb-0.5"
                    ),
                    P(log.get("summary") or action_name, cls="text-xs text-secondary leading-snug"),
                    cls="min-w-0 flex-1"
                ),
                cls="flex items-start gap-3 flex-1 min-w-0"
            ),
            Div(
                Span(icon("history", "text-xs mr-1 text-muted"), created_str, cls="text-[11px] font-mono text-muted flex items-center"),
                cls="text-right shrink-0"
            ),
            cls="flex items-center justify-between p-3.5 rounded-xl bg-white/5 hover:bg-white/10 transition-colors gap-4"
        )

    log_list = card(
        Div(
            icon("verified_user", "text-emerald-400 text-sm mr-1.5"),
            Span("The activity log is cryptographically permanent and cannot be modified or deleted by any user.", cls="text-xs font-mono text-emerald-300"),
            cls="flex items-center p-3 rounded-lg bg-emerald-950/40 border border-emerald-500/20 mb-4"
        ),
        Div(
            *[log_row(l) for l in logs] or [
                Div(P("No activity logged yet.", cls="text-muted text-sm text-center py-12"))
            ],
            cls="space-y-2"
        )
    )

    return page(session, u, "Activity Logs", header, filter_chips, log_list)

@rt("/activity/export.csv", methods=["GET"])
def activity_export_csv(session):
    u = current_user(session)
    if not u or RANKS.get(u["role"], 1) < 4:
        return go("/activity")

    try:
        logs = supabase.table("activity").select("*").order("created_at", desc=True).limit(500).execute().data or []
    except Exception:
        logs = []

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Timestamp", "Member ID", "Member Name", "Role", "Section", "Action", "Summary"])

    for l in logs:
        writer.writerow([
            l.get("created_at", ""),
            l.get("member_id", ""),
            l.get("member_name", ""),
            l.get("role", ""),
            l.get("section", ""),
            l.get("action", ""),
            l.get("summary", "")
        ])

    return Response(
        output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=technoverse_audit_log.csv"}
    )
