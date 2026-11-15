import os
from datetime import datetime, timezone
from fasthtml.common import *
from core import rt, current_user, go, supabase
from components import *
from auth import log_activity

@rt("/president", methods=["GET"])
def president_dashboard(session, msg: str = "", error: str = ""):
    user = current_user(session)
    if not user:
        return go("/login")
    if user["role"] not in ["president", "club_coordinator"]:
        return go("/?error=Access+Restricted:+The+Presidential+Desk+is+exclusively+reserved+for+the+Club+President.")

    # Fetch recent presidential decrees / directives from announcements or activity
    try:
        directives = supabase.table("activity").select("*").eq("section", "president").order("created_at", desc=True).limit(10).execute().data or []
    except Exception as e:
        print("Error fetching presidential directives:", e)
        directives = []

    # Fetch pending high-value expenses for presidential sanction (> 5000 or pending)
    try:
        expenses = supabase.table("expenses").select("*").order("created_at", desc=True).limit(6).execute().data or []
    except Exception as e:
        print("Error fetching expenses for president:", e)
        expenses = []

    # Fetch team leads overview
    try:
        leads = supabase.table("members").select("name, roll, role, branch, designation").in_("role", ["vice_president", "secretary", "treasurer", "technical_lead", "event_coordinator"]).execute().data or []
    except Exception as e:
        print("Error fetching leads:", e)
        leads = []

    return page(
        session, user, "Presidential Governance Desk",
        # Hero Banner
        card(
            Div(
                Div(
                    Div(
                        Span("PRESIDENTIAL EXECUTIVE DESK", cls="text-xs font-mono font-bold tracking-wider text-amber-400 uppercase bg-amber-500/10 border border-amber-500/20 px-3 py-1 rounded-full inline-block mb-2"),
                        H1("Club Governance & Executive Authority", cls="text-2xl md:text-3xl font-heading font-bold text-white"),
                        P(f"Executive Session: {user['name']} • Official President of Technoverse Club", cls="text-slate-300 text-sm mt-1"),
                        cls="space-y-1"
                    ),
                    Div(
                        A(
                            icon("download", "text-sm mr-1.5"), "Official Credentials PDF",
                            href="/Technoverse_Top_Roles_Credentials.pdf", target="_blank",
                            cls="inline-flex items-center text-xs font-mono font-semibold bg-white/[0.05] hover:bg-white/[0.1] text-amber-400 border border-amber-500/30 px-3.5 py-2 rounded-xl transition-all"
                        ),
                        A(
                            icon("person_add", "text-sm mr-1.5"), "Provision New Members",
                            href="/team",
                            cls="inline-flex items-center text-xs font-mono font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-600/25 px-3.5 py-2 rounded-xl transition-all"
                        ),
                        cls="flex flex-wrap items-center gap-2 mt-4 md:mt-0"
                    ),
                    cls="flex flex-col md:flex-row md:items-center justify-between gap-4"
                ),
                cls="relative z-10"
            ),
            cls="relative overflow-hidden mb-8 border border-amber-500/20 bg-gradient-to-br from-[#0f172a] via-[#111c38] to-[#0d1426]"
        ),

        # Alerts
        Div(msg, cls="bg-emerald-900/40 border border-emerald-500/30 p-4 rounded-xl text-emerald-200 text-sm mb-6") if msg else "",
        Div(error, cls="bg-red-900/40 border border-red-500/30 p-4 rounded-xl text-red-200 text-sm mb-6") if error else "",

        # Top Executive Metrics
        Div(
            stat_card("Constitutional Authority", "PRESIDENT", "gavel", "Rank 4 Supreme Executive"),
            stat_card("Active Directives", len(directives), "campaign", "Published Executive Mandates"),
            stat_card("Standing Wings", "4 WINGS", "account_tree", "Tech, Events, Finance, Secretariat"),
            stat_card("Charter Status", "AFFILIATED", "verified", "Hari University Technical Body"),
            cls="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
        ),

        # Main 2-Column Grid
        Div(
            # Left Column: Executive Directive Dispatcher
            Div(
                card(
                    Div(
                        icon("campaign", "text-amber-400 text-xl"),
                        H2("Issue Presidential Directive", cls="text-lg font-heading font-bold text-white"),
                        cls="flex items-center gap-2.5 mb-1"
                    ),
                    P("Issue official executive orders or strategic mandates binding across all club wings.", cls="text-xs text-slate-400 mb-5"),
                    Form(
                        input_field("Directive Title", "title", placeholder="e.g. Executive Mandate: Hackathon Sprint Readiness"),
                        select_field("Classification Level", "category", [
                            ("STRATEGIC_MANDATE", "Strategic Executive Mandate (Immediate Binding)"),
                            ("UNIVERSITY_POLICY", "Hari University Liaison Directive"),
                            ("INTER_WING_DIRECTIVE", "Inter-Wing Operational Directive"),
                            ("PRESIDENTIAL_COMMENDATION", "Presidential Commendation & Recognition")
                        ]),
                        select_field("Target Audience", "target_wing", [
                            ("ALL_WINGS", "All Wings (Technical, Events, Treasury, Secretariat)"),
                            ("TECHNICAL_WING", "Technical Wing (Leads: Harsha & Manikanta)"),
                            ("EVENT_WING", "Event Management Wing (Coordinators: Swetha, Thanusree, Sahasra)"),
                            ("TREASURY", "Treasury & Finance (Treasurer: Chaitanya)"),
                            ("SECRETARIAT", "Secretariat & Records (Secretary: B. Sariyu)")
                        ]),
                        textarea_field("Executive Directive Text & Actionables", "body", placeholder="Provide detailed executive instructions, deadlines, and deliverables..."),
                        btn_primary(icon("send", "text-sm mr-1"), "Broadcast Presidential Directive", type="submit", cls="w-full py-2.5 font-semibold text-sm"),
                        method="post",
                        action="/president/directive"
                    ),
                    cls="mb-8"
                ),

                # Feed of active directives
                card(
                    Div(
                        icon("history_edu", "text-blue-400 text-xl"),
                        H3("Official Directives Log", cls="text-base font-heading font-bold text-white"),
                        cls="flex items-center gap-2.5 mb-4"
                    ),
                    Div(
                        *[
                            Div(
                                Div(
                                    Span(d.get("summary", "Presidential Directive"), cls="text-sm font-semibold text-white block"),
                                    Span(f"Issued by {d.get('member_name', 'President')} • {d.get('created_at', '')[:10]}", cls="text-xs text-slate-400 font-mono mt-0.5 block"),
                                    P(d.get("new_value") or "Executive Directive Dispatched to Committee", cls="text-xs text-slate-300 mt-2 bg-white/[0.03] p-2.5 rounded-lg border border-white/5"),
                                    cls="flex-1"
                                ),
                                cls="p-3.5 rounded-xl border border-white/[0.06] bg-white/[0.02] mb-3 last:mb-0 hover:bg-white/[0.04] transition-all"
                            ) for d in directives
                        ] if directives else [
                            Div(
                                icon("verified", "text-3xl text-slate-500 mb-2"),
                                P("No directives issued this term yet.", cls="text-sm text-slate-400 font-mono"),
                                cls="text-center py-8"
                            )
                        ],
                        cls="space-y-2"
                    )
                )
            ),

            # Right Column: High-Value Sanctions & Standing Wing Leads
            Div(
                # High-Value Financial Sanctions
                card(
                    Div(
                        icon("account_balance", "text-emerald-400 text-xl"),
                        H2("Presidential Budget Sanctions", cls="text-lg font-heading font-bold text-white"),
                        cls="flex items-center gap-2.5 mb-1"
                    ),
                    P("Exclusive presidential oversight and executive sign-off for club funds.", cls="text-xs text-slate-400 mb-4"),
                    Div(
                        *[
                            Div(
                                Div(
                                    Div(
                                        Span(e.get("title", "Expense Request"), cls="text-sm font-semibold text-white block"),
                                        Span(f"Category: {e.get('category', 'Club')}", cls="text-xs text-slate-400 font-mono"),
                                        cls="flex-1"
                                    ),
                                    Div(
                                        Span(format_inr(e.get("amount", 0)), cls="text-base font-bold font-mono text-emerald-400"),
                                        badge(e.get("status", "pending").upper(), "done" if e.get("status") == "approved" else "amber"),
                                        cls="text-right flex flex-col items-end gap-1"
                                    ),
                                    cls="flex items-start justify-between gap-3"
                                ),
                                Div(
                                    Form(
                                        Input(type="hidden", name="expense_id", value=str(e.get("id"))),
                                        btn_success(icon("check", "text-xs mr-1"), "Grant Presidential Sanction", type="submit", cls="text-xs py-1.5 px-3 w-full"),
                                        method="post",
                                        action="/president/sanction"
                                    ) if e.get("status") != "approved" else Span("✓ Sanctioned & Approved", cls="text-xs text-emerald-400 font-mono font-semibold"),
                                    cls="mt-3 pt-2.5 border-t border-white/[0.05]"
                                ),
                                cls="p-3.5 rounded-xl border border-white/[0.06] bg-white/[0.02] mb-3 last:mb-0"
                            ) for e in expenses
                        ] if expenses else [
                            Div(
                                P("No pending expense sanctions. Treasury is clear.", cls="text-sm text-slate-400 font-mono text-center py-6")
                            )
                        ]
                    ),
                    cls="mb-8"
                ),

                # Standing Wing Leadership
                card(
                    Div(
                        icon("groups", "text-indigo-400 text-xl"),
                        H2("Executive Wing Leadership", cls="text-lg font-heading font-bold text-white"),
                        cls="flex items-center gap-2.5 mb-1"
                    ),
                    P("Direct reporting committee officers appointed under your executive tenure.", cls="text-xs text-slate-400 mb-4"),
                    Div(
                        *[
                            Div(
                                avatar(m.get("name")),
                                Div(
                                    Span(m.get("name"), cls="text-sm font-semibold text-white block leading-tight"),
                                    Span(f"{m.get('designation') or m.get('role').replace('_', ' ').title()} • {m.get('branch')}", cls="text-xs text-slate-400 block mt-0.5"),
                                    cls="flex-1"
                                ),
                                badge(m.get("roll"), "secondary"),
                                cls="flex items-center gap-3 p-2.5 rounded-xl border border-white/[0.04] bg-white/[0.01] hover:bg-white/[0.03] transition-all"
                            ) for m in leads
                        ],
                        cls="space-y-2.5"
                    ),
                    A(
                        icon("manage_accounts", "text-sm mr-1.5"), "Open Full Committee Manager",
                        href="/team",
                        cls="mt-5 block text-center text-xs font-mono text-blue-400 hover:text-blue-300 py-2 border border-blue-500/20 rounded-xl bg-blue-500/5 transition-all"
                    )
                )
            ),
            cls="grid grid-cols-1 lg:grid-cols-2 gap-8"
        )
    )

@rt("/president/directive", methods=["POST"])
def presidential_directive_post(session, title: str, category: str, target_wing: str, body: str):
    user = current_user(session)
    if not user or user["role"] not in ["president", "club_coordinator"]:
        return go("/login")
    
    clean_title = (title or "").strip()
    clean_body = (body or "").strip()
    if not clean_title or not clean_body:
        return go("/president?error=Title+and+directive+content+are+required.")

    now_iso = datetime.now(timezone.utc).isoformat()
    summary_text = f"Presidential Directive: {clean_title} [{category}] -> {target_wing}"

    # Log to activity
    try:
        supabase.table("activity").insert({
            "member_id": user["id"],
            "member_name": user["name"],
            "role": user["role"],
            "action": "presidential_directive",
            "section": "president",
            "summary": summary_text,
            "new_value": clean_body,
            "created_at": now_iso
        }).execute()
    except Exception as e:
        print("Error recording presidential directive in activity:", e)

    # Post to announcements
    try:
        announcement_text = f"📢 [PRESIDENTIAL DIRECTIVE] {clean_title} ({target_wing})\n\n{clean_body}\n\n— Karthik, President (Technoverse Club)"
        supabase.table("announcements").insert({
            "body": announcement_text,
            "pinned": True,
            "created_by": user["id"],
            "created_at": now_iso
        }).execute()
    except Exception as e:
        print("Error posting directive to announcements:", e)

    return go(f"/president?msg=Presidential+Directive+'{clean_title}'+successfully+broadcast+to+{target_wing}.")

@rt("/president/sanction", methods=["POST"])
def presidential_sanction_post(session, expense_id: str):
    user = current_user(session)
    if not user or user["role"] not in ["president", "club_coordinator"]:
        return go("/login")
    
    try:
        supabase.table("expenses").update({"status": "approved"}).eq("id", expense_id).execute()
        log_activity(session, "presidential_sanction", "finance", expense_id, f"President {user['name']} granted executive sanction to expense #{expense_id}")
    except Exception as e:
        print("Error granting presidential sanction:", e)
        return go(f"/president?error=Failed+to+grant+sanction:+{str(e)[:100]}")

    return go(f"/president?msg=Presidential+Sanction+granted+for+expense+#{expense_id}.")
