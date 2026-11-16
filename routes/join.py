from fasthtml.common import *
from core import rt, current_user, go, supabase
from components import *
from auth import RANKS, hash_pw, log_activity
from cache import get_cached, set_cached, invalidate_cache

@rt("/join-requests", methods=["GET"])
def join_requests_get(session, status_filter: str = "all"):
    u = current_user(session)
    if not u:
        return go("/login")
    role = session.get("view_as") or u["role"]
    rank = RANKS.get(role, 1)

    if rank < 4:
        return page(session, u, "Join Requests", card(H2("Executive Access Only", cls="font-heading font-bold text-xl text-red-400 mb-2"), P("Recruitment review and applicant onboarding is restricted to Vice Presidents, Presidents, and the Club Coordinator.", cls="text-sm text-secondary")))

    reqs = get_cached("join_requests", ttl=15)
    if reqs is None:
        try:
            reqs = supabase.table("join_requests").select("*").order("created_at", desc=True).execute().data or []
            set_cached("join_requests", reqs)
        except Exception:
            reqs = []

    if status_filter != "all":
        reqs = [r for r in reqs if r.get("status") == status_filter]

    def request_card(r):
        rid = r["id"]
        st = r.get("status", "pending")
        can_decide = (st == "pending") and not session.get("view_as")

        actions = Div(
            Form(
                Input(type="hidden", name="action", value="approve"),
                btn_success(icon("check", "text-xs"), "Approve & Onboard", type="submit", cls="text-xs py-1.5 px-3"),
                method="post", action=f"/join-requests/{rid}/decision", cls="inline-block"
            ),
            Form(
                Input(type="hidden", name="action", value="reject"),
                btn_danger(icon("close", "text-xs"), "Reject", type="submit", cls="text-xs py-1.5 px-3"),
                method="post", action=f"/join-requests/{rid}/decision", cls="inline-block"
            ),
            cls="flex items-center gap-2 mt-4"
        ) if can_decide else badge(st.upper(), st)

        return card(
            Div(
                Div(
                    H3(r.get("name", "Applicant"), cls="font-heading font-bold text-base"),
                    P(f"Roll: {r.get('roll', '')} • Branch: {r.get('branch', 'CSE')} • Year {r.get('year', 1)}", cls="text-xs text-muted font-mono mt-0.5"),
                    cls="flex-1"
                ),
                badge(st.upper(), st) if can_decide else "",
                cls="flex items-center justify-between mb-3"
            ),
            P(r.get("message", "No statement of interest provided."), cls="text-xs text-secondary bg-white/5 p-3 rounded-lg leading-relaxed"),
            actions,
            p="p-5"
        )

    modal = Div(
        Div(onclick="document.getElementById('applicant-modal').classList.add('hidden')", cls="absolute inset-0 bg-black/60 backdrop-blur-sm"),
        card(
            Div(
                H3("Add Candidate Application", cls="font-heading font-bold text-xl"),
                Button(icon("close"), onclick="document.getElementById('applicant-modal').classList.add('hidden')", type="button", cls="text-muted hover:text-white bg-transparent border-0 cursor-pointer"),
                cls="flex items-center justify-between mb-4"
            ),
            Form(
                input_field("Applicant Full Name", "name", placeholder="e.g. Priyanshu Patel", required=True),
                Div(
                    input_field("Roll Number", "roll", placeholder="e.g. 26ET105088", required=True),
                    input_field("Branch / Dept", "branch", placeholder="e.g. IT", required=True),
                    cls="grid grid-cols-2 gap-3"
                ),
                input_field("Year of Study", "year", type="number", value="1", required=True),
                textarea_field("Statement of Interest / Skills", "message", placeholder="Why does the candidate want to join Technoverse Club?...", rows=3),
                Div(
                    btn_ghost("Cancel", type="button", onclick="document.getElementById('applicant-modal').classList.add('hidden')"),
                    btn_primary("Submit Application", type="submit", loading_text="Submitting..."),
                    cls="flex justify-end gap-3 mt-6"
                ),
                method="post", action="/join-requests/new"
            ),
            cls="relative z-10 w-full max-w-lg mx-auto mt-16"
        ),
        id="applicant-modal",
        cls="fixed inset-0 z-50 flex items-center justify-center p-4 hidden"
    )

    header = Div(
        Div(
            H1("Join Requests & Recruitment", cls="font-heading font-bold text-2xl"),
            P("Review student applications and induct approved candidates into core membership", cls="text-sm text-secondary"),
            cls="flex-1"
        ),
        Div(
            btn_primary(
                icon("person_add", "text-sm"), "Add Candidate",
                onclick="document.getElementById('applicant-modal').classList.remove('hidden')",
                type="button"
            ) if not session.get("view_as") else "",
            cls="flex items-center gap-3"
        ),
        cls="flex flex-wrap items-center justify-between gap-4 mb-6"
    )

    grid = Div(
        *[request_card(r) for r in reqs] or [
            Div(P("No applicant records in inbox.", cls="text-muted text-sm text-center py-12"), cls="col-span-full")
        ],
        cls="grid grid-cols-1 md:grid-cols-2 gap-4"
    )

    return page(session, u, "Join Requests", header, grid, modal)

@rt("/join-requests/new", methods=["POST"])
def join_new_post(session, name: str, roll: str, branch: str, year: int, message: str = ""):
    u = current_user(session)
    if not u or session.get("view_as"):
        return go("/login")

    payload = {
        "name": name.strip(),
        "roll": roll.strip().upper(),
        "branch": branch.strip(),
        "year": int(year or 1),
        "message": message.strip() if message else None,
        "status": "pending"
    }

    try:
        res = supabase.table("join_requests").insert(payload).execute()
        if res.data:
            invalidate_cache("join_")
            log_activity(session, "candidate_applied", "join_requests", res.data[0]["id"], f"Candidate application received: {name.strip()}")
    except Exception as e:
        print("Application addition error:", e)

    return go("/join-requests")

@rt("/join-requests/{rid}/decision", methods=["POST"])
def join_decision_post(session, rid: int, action: str):
    u = current_user(session)
    if not u or session.get("view_as") or RANKS.get(u["role"], 1) < 4:
        return go("/join-requests")

    new_st = "approved" if action == "approve" else "rejected"
    try:
        # Fetch candidate info
        cand = supabase.table("join_requests").select("*").eq("id", rid).single().execute().data
        if cand and new_st == "approved":
            # Provision member account
            default_pw = "welcome2026"
            supabase.table("members").upsert({
                "name": cand["name"],
                "roll": cand["roll"],
                "email": f"{cand['roll'].lower()}@college.edu",
                "branch": cand.get("branch"),
                "year": cand.get("year"),
                "role": "member",
                "pw_hash": hash_pw(default_pw),
                "active": True
            }).execute()
            invalidate_cache("team_")
            invalidate_cache("user_")
            invalidate_cache("members_")

        supabase.table("join_requests").update({"status": new_st, "decided_by": u["id"]}).eq("id", rid).execute()
        invalidate_cache("join_")
        log_activity(session, f"join_request_{new_st}", "join_requests", rid, f"{new_st.title()} candidate {cand.get('name') if cand else rid}")
    except Exception as e:
        print("Candidate decision error:", e)

    return go("/join-requests")
