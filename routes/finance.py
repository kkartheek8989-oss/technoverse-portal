from fasthtml.common import *
from core import rt, current_user, go, supabase
from components import *
from auth import RANKS, can, log_activity
from cache import get_cached, set_cached, invalidate_cache

@rt("/finance", methods=["GET"])
def finance_get(session, tab: str = "expenses"):
    u = current_user(session)
    if not u:
        return go("/login")
    role = session.get("view_as") or u["role"]
    rank = RANKS.get(role, 1)

    if rank < 3 and role != "treasurer":
        # Restricted section
        return page(session, u, "Club Finance", card(H2("Access Restricted", cls="font-heading font-bold text-xl text-red-400 mb-2"), P("You do not have permission to view the club finance ledger. Only Treasurers and Executive Board members have access.", cls="text-sm text-secondary")))

    expenses = get_cached("finance_expenses", ttl=15)
    if expenses is None:
        try:
            expenses = supabase.table("expenses").select("*, submitter:submitted_by(name, roll)").order("created_at", desc=True).execute().data or []
            set_cached("finance_expenses", expenses)
        except Exception:
            expenses = []

    sponsorships = get_cached("finance_sponsorships", ttl=15)
    if sponsorships is None:
        try:
            sponsorships = supabase.table("sponsorships").select("*").order("created_at", desc=True).execute().data or []
            set_cached("finance_sponsorships", sponsorships)
        except Exception:
            sponsorships = []

    # Financial calculations
    total_spent = sum(float(e.get("amount") or 0) for e in expenses if e.get("status") == "approved")
    pending_spent = sum(float(e.get("amount") or 0) for e in expenses if e.get("status") == "pending")
    total_sponsorships = sum(float(s.get("amount") or 0) for s in sponsorships if s.get("status") == "received")
    total_pledged = sum(float(s.get("amount") or 0) for s in sponsorships if s.get("status") == "pledged")

    initial_budget = 150000.0  # Default club fiscal pool
    available_balance = initial_budget + total_sponsorships - total_spent

    can_manage = (role == "treasurer" or rank >= 4) and not session.get("view_as")

    header = Div(
        Div(
            H1("Club Finance & Ledger", cls="font-heading font-bold text-2xl"),
            P("Transparent balance tracking, sponsorship pipeline, and expense authorizations", cls="text-sm text-secondary"),
            cls="flex-1"
        ),
        Div(
            btn_primary(
                icon("receipt_long", "text-sm"), "Submit Expense",
                onclick="document.getElementById('expense-modal').classList.remove('hidden')",
                type="button"
            ) if can_manage else "",
            btn_ghost(
                icon("handshake", "text-sm"), "Record Sponsor",
                onclick="document.getElementById('sponsor-modal').classList.remove('hidden')",
                type="button"
            ) if can_manage else "",
            cls="flex items-center gap-3"
        ),
        cls="flex flex-wrap items-center justify-between gap-4 mb-6"
    )

    stats = Div(
        stat_card("Available Balance", format_inr(available_balance), "account_balance", "Current operating reserves"),
        stat_card("Total Disbursed", format_inr(total_spent), "payments", f"{format_inr(pending_spent)} pending approval"),
        stat_card("Sponsorship Funds", format_inr(total_sponsorships), "volunteer_activism", f"{format_inr(total_pledged)} pledged"),
        cls="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6"
    )

    def expense_row(e):
        eid = e["id"]
        status = e.get("status", "pending")
        amount_fmt = format_inr(e.get("amount", 0))
        sub_name = e.get("submitter", {}).get("name") if e.get("submitter") else "Member"

        auth_actions = Div(
            Form(
                Input(type="hidden", name="action_type", value="approved"),
                btn_success(icon("check", "text-xs"), "Approve", type="submit", cls="text-xs py-1 px-2.5"),
                method="post", action=f"/finance/expenses/{eid}/authorize", cls="inline-block"
            ),
            Form(
                Input(type="hidden", name="action_type", value="rejected"),
                btn_danger(icon("close", "text-xs"), "Reject", type="submit", cls="text-xs py-1 px-2.5"),
                method="post", action=f"/finance/expenses/{eid}/authorize", cls="inline-block"
            ),
            cls="flex items-center gap-2"
        ) if status == "pending" and can_manage else badge(status.upper(), status)

        return Div(
            Div(
                Div(
                    H4(e.get("description", "Club Expense"), cls="font-semibold text-sm"),
                    P(f"Submitted by {sub_name} • {(e.get('created_at') or '')[:10]}", cls="text-xs text-muted font-mono"),
                    cls="truncate"
                ),
                cls="flex-1 min-w-0"
            ),
            Div(
                Div(amount_fmt, cls="font-mono font-bold text-base text-right"),
                auth_actions,
                cls="flex items-center gap-4"
            ),
            cls="flex items-center justify-between p-3.5 rounded-xl bg-white/5 hover:bg-white/10 transition-colors"
        )

    def sponsor_row(s):
        status = s.get("status", "pledged")
        return Div(
            Div(
                H4(s.get("sponsor", "Corporate Partner"), cls="font-semibold text-sm"),
                P(f"Date: {(s.get('created_at') or '')[:10]}", cls="text-xs text-muted font-mono"),
                cls="flex-1"
            ),
            Div(
                Div(format_inr(s.get("amount", 0)), cls="font-mono font-bold text-base text-emerald-400"),
                badge(status.upper(), "done" if status == "received" else "amber"),
                cls="flex items-center gap-3"
            ),
            cls="flex items-center justify-between p-3.5 rounded-xl bg-white/5 hover:bg-white/10 transition-colors"
        )

    expenses_card = card(
        H3("Expense Claims & Authorizations", cls="font-heading font-semibold text-lg mb-4"),
        Div(
            *[expense_row(e) for e in expenses] or [P("No expenses submitted yet.", cls="text-muted text-sm py-4 text-center")],
            cls="space-y-2"
        ),
        cls="mb-6"
    )

    sponsors_card = card(
        H3("Sponsorships & Contributions", cls="font-heading font-semibold text-lg mb-4"),
        Div(
            *[sponsor_row(s) for s in sponsorships] or [P("No sponsorships recorded yet.", cls="text-muted text-sm py-4 text-center")],
            cls="space-y-2"
        )
    )

    expense_modal = Div(
        Div(onclick="document.getElementById('expense-modal').classList.add('hidden')", cls="absolute inset-0 bg-black/60 backdrop-blur-sm"),
        card(
            Div(
                H3("Submit Expense Claim", cls="font-heading font-bold text-xl"),
                Button(icon("close"), onclick="document.getElementById('expense-modal').classList.add('hidden')", type="button", cls="text-muted hover:text-white bg-transparent border-0 cursor-pointer"),
                cls="flex items-center justify-between mb-4"
            ),
            Form(
                input_field("Expense Description", "description", placeholder="e.g. Refreshments for CodeX Workshop", required=True),
                input_field("Amount (in ₹ INR)", "amount", type="number", placeholder="e.g. 3500", required=True),
                Div(
                    btn_ghost("Cancel", type="button", onclick="document.getElementById('expense-modal').classList.add('hidden')"),
                    btn_primary("Submit for Authorization", type="submit", loading_text="Submitting Expense..."),
                    cls="flex justify-end gap-3 mt-6"
                ),
                method="post", action="/finance/expenses/new"
            ),
            cls="relative z-10 w-full max-w-lg mx-auto mt-16"
        ),
        id="expense-modal",
        cls="fixed inset-0 z-50 flex items-center justify-center p-4 hidden"
    )

    sponsor_modal = Div(
        Div(onclick="document.getElementById('sponsor-modal').classList.add('hidden')", cls="absolute inset-0 bg-black/60 backdrop-blur-sm"),
        card(
            Div(
                H3("Record Sponsorship Pledge", cls="font-heading font-bold text-xl"),
                Button(icon("close"), onclick="document.getElementById('sponsor-modal').classList.add('hidden')", type="button", cls="text-muted hover:text-white bg-transparent border-0 cursor-pointer"),
                cls="flex items-center justify-between mb-4"
            ),
            Form(
                input_field("Sponsor / Partner Name", "sponsor", placeholder="e.g. TechCorp Labs", required=True),
                input_field("Contribution Amount (in ₹ INR)", "amount", type="number", placeholder="e.g. 50000", required=True),
                select_field("Payment Status", "status", [("received", "Received / Disbursed"), ("pledged", "Pledged (Pending Transfer)")]),
                Div(
                    btn_ghost("Cancel", type="button", onclick="document.getElementById('sponsor-modal').classList.add('hidden')"),
                    btn_primary("Save Record", type="submit", loading_text="Saving Record..."),
                    cls="flex justify-end gap-3 mt-6"
                ),
                method="post", action="/finance/sponsorships/new"
            ),
            cls="relative z-10 w-full max-w-lg mx-auto mt-16"
        ),
        id="sponsor-modal",
        cls="fixed inset-0 z-50 flex items-center justify-center p-4 hidden"
    )

    return page(session, u, "Club Finance", header, stats, expenses_card, sponsors_card, expense_modal, sponsor_modal)

@rt("/finance/expenses/new", methods=["POST"])
def finance_expense_new(session, description: str, amount: float):
    u = current_user(session)
    if not u or session.get("view_as"):
        return go("/login")
    if u["role"] != "treasurer" and RANKS.get(u["role"], 1) < 3:
        return go("/finance")

    payload = {
        "description": description.strip(),
        "amount": float(amount or 0),
        "status": "pending",
        "submitted_by": u["id"]
    }
    try:
        res = supabase.table("expenses").insert(payload).execute()
        if res.data:
            invalidate_cache("finance_")
            log_activity(session, "expense_submitted", "finance", res.data[0]["id"], f"Submitted expense {format_inr(amount)}: {description.strip()}")
    except Exception as e:
        print("Expense submission error:", e)

    return go("/finance")

@rt("/finance/expenses/{eid}/authorize", methods=["POST"])
def finance_expense_authorize(session, eid: int, action_type: str):
    u = current_user(session)
    if not u or session.get("view_as"):
        return go("/login")
    if u["role"] != "treasurer" and RANKS.get(u["role"], 1) < 4:
        return go("/finance")

    new_st = "approved" if action_type == "approved" else "rejected"
    try:
        supabase.table("expenses").update({"status": new_st, "approved_by": u["id"]}).eq("id", eid).execute()
        invalidate_cache("finance_")
        log_activity(session, f"expense_{new_st}", "finance", eid, f"{new_st.title()} expense #{eid}")
    except Exception as e:
        print("Expense authorization error:", e)

    return go("/finance")

@rt("/finance/sponsorships/new", methods=["POST"])
def finance_sponsor_new(session, sponsor: str, amount: float, status: str = "received"):
    u = current_user(session)
    if not u or session.get("view_as"):
        return go("/login")
    if u["role"] != "treasurer" and RANKS.get(u["role"], 1) < 4:
        return go("/finance")

    payload = {
        "sponsor": sponsor.strip(),
        "amount": float(amount or 0),
        "status": status
    }
    try:
        res = supabase.table("sponsorships").insert(payload).execute()
        if res.data:
            invalidate_cache("finance_")
            log_activity(session, "sponsorship_added", "finance", res.data[0]["id"], f"Added sponsorship {format_inr(amount)} from {sponsor.strip()}")
    except Exception as e:
        print("Sponsorship addition error:", e)

    return go("/finance")
