from fasthtml.common import *
from starlette.requests import Request
from core import rt, current_user, go, supabase
from components import *
from auth import log_activity
from site_config import get_site_config, bulk_update_settings, reset_settings_to_defaults

@rt("/admin-control", methods=["GET"])
def admin_control_get(session, msg: str = "", error: str = ""):
    u = current_user(session)
    if not u:
        return go("/login")
    if u["role"] not in ["president", "club_coordinator"]:
        return go("/?error=Access+Restricted:+The+Admin+Control+suite+is+exclusively+restricted+to+the+Club+Coordinator+and+President.")

    cfg = get_site_config(force_reload=True)

    header = card(
        Div(
            Div(
                Div(
                    Span("SECRET CMS • EXECUTIVE EDITING SUITE", cls="text-[11px] font-mono font-bold tracking-wider text-red-400 uppercase bg-red-500/10 border border-red-500/30 px-3 py-1 rounded-full inline-block mb-2"),
                    H1("Admin Control & Website Content Manager", cls="text-2xl md:text-3xl font-heading font-bold text-white"),
                    P("Autonomous website maintenance suite. Edit any section of the website live without touching code or calling AI.", cls="text-slate-300 text-sm mt-1"),
                    cls="space-y-1"
                ),
                Div(
                    Form(
                        btn_danger(icon("restart_alt", "text-sm mr-1"), "Reset University Defaults", type="submit", cls="text-xs py-2 px-3.5"),
                        method="post", action="/admin-control/reset",
                        onsubmit="return confirm('Warning: Reset all website content back to official University defaults?');"
                    ),
                    A(
                        btn_ghost(icon("visibility", "text-sm mr-1"), "Preview Live Home", cls="text-xs py-2 px-3.5"),
                        href="/", target="_blank"
                    ),
                    cls="flex flex-wrap items-center gap-2 mt-4 md:mt-0"
                ),
                cls="flex flex-col md:flex-row md:items-center justify-between gap-4"
            ),
            cls="relative z-10"
        ),
        cls="relative overflow-hidden mb-8 border border-red-500/20 bg-gradient-to-br from-[#1a0f1f] via-[#120f24] to-[#080c14]"
    )

    alerts_div = (
        Div(msg, cls="bg-emerald-900/40 border border-emerald-500/30 p-4 rounded-xl text-emerald-200 text-sm mb-6") if msg else
        (Div(error, cls="bg-red-900/40 border border-red-500/30 p-4 rounded-xl text-red-200 text-sm mb-6") if error else "")
    )

    # Section 1: Identity & University Affiliation
    sec_identity = card(
        Div(
            icon("account_balance", "text-amber-400 text-xl"),
            H2("1. University Affiliation & Hero Identity", cls="text-lg font-heading font-bold text-white"),
            cls="flex items-center gap-2.5 mb-1"
        ),
        P("Live branding, university status, and opening hero headline displayed on the home page.", cls="text-xs text-slate-400 mb-5"),
        Div(
            input_field("University Name", "university_name", value=cfg.get("university_name")),
            input_field("University Status (e.g. Deemed to be University)", "university_status", value=cfg.get("university_status")),
            cls="grid grid-cols-1 md:grid-cols-2 gap-4"
        ),
        Div(
            input_field("Website Title / Portal Name", "site_title", value=cfg.get("site_title")),
            input_field("Official Tagline / Motto", "site_tagline", value=cfg.get("site_tagline")),
            cls="grid grid-cols-1 md:grid-cols-2 gap-4"
        ),
        input_field("Hero Opening Headline", "hero_headline", value=cfg.get("hero_headline")),
        textarea_field("Hero Mission Description", "hero_subtext", value=cfg.get("hero_subtext")),
        input_field("Official Footer Text", "footer_text", value=cfg.get("footer_text")),
        cls="mb-8"
    )

    # Section 2: The 4 Technical Pillars
    sec_pillars = card(
        Div(
            icon("view_quilt", "text-blue-400 text-xl"),
            H2("2. Core Technical Pillars", cls="text-lg font-heading font-bold text-white"),
            cls="flex items-center gap-2.5 mb-1"
        ),
        P("Edit the four core engineering tracks presented to students and faculty.", cls="text-xs text-slate-400 mb-5"),
        Div(
            Div(
                input_field("Pillar 1 Title", "pillar1_title", value=cfg.get("pillar1_title")),
                textarea_field("Pillar 1 Description", "pillar1_desc", value=cfg.get("pillar1_desc")),
                cls="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]"
            ),
            Div(
                input_field("Pillar 2 Title", "pillar2_title", value=cfg.get("pillar2_title")),
                textarea_field("Pillar 2 Description", "pillar2_desc", value=cfg.get("pillar2_desc")),
                cls="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]"
            ),
            Div(
                input_field("Pillar 3 Title", "pillar3_title", value=cfg.get("pillar3_title")),
                textarea_field("Pillar 3 Description", "pillar3_desc", value=cfg.get("pillar3_desc")),
                cls="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]"
            ),
            Div(
                input_field("Pillar 4 Title", "pillar4_title", value=cfg.get("pillar4_title")),
                textarea_field("Pillar 4 Description", "pillar4_desc", value=cfg.get("pillar4_desc")),
                cls="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]"
            ),
            cls="grid grid-cols-1 md:grid-cols-2 gap-4"
        ),
        cls="mb-8"
    )

    # Section 3: Announcements & Global Urgent Alert Banner
    sec_announcements = card(
        Div(
            icon("campaign", "text-amber-400 text-xl"),
            H2("3. Announcements & Emergency Alert Banner", cls="text-lg font-heading font-bold text-white"),
            cls="flex items-center gap-2.5 mb-1"
        ),
        P("Display a persistent high-priority notification banner at the top of the portal.", cls="text-xs text-slate-400 mb-5"),
        Div(
            select_field("Emergency Alert Banner Active?", "alert_banner_enabled", [
                ("false", "Disabled (Do not show banner)"),
                ("true", "Active (Show banner at top of portal)")
            ], selected=cfg.get("alert_banner_enabled")),
            select_field("Alert Severity Color", "alert_banner_type", [
                ("amber", "Amber Warning (High Visibility)"),
                ("red", "Red Critical (Urgent Emergency)"),
                ("primary", "Blue Info (General Executive Notice)"),
                ("emerald", "Green Success (Milestone Celebration)")
            ], selected=cfg.get("alert_banner_type")),
            cls="grid grid-cols-1 md:grid-cols-2 gap-4"
        ),
        input_field("Emergency Alert Message", "alert_banner_text", value=cfg.get("alert_banner_text")),
        textarea_field("Live Announcement Ticker Content", "announcement_ticker", value=cfg.get("announcement_ticker")),
        cls="mb-8"
    )

    # Section 4: Club Operating Parameters & Maintenance Mode
    sec_ops = card(
        Div(
            icon("settings_suggest", "text-emerald-400 text-xl"),
            H2("4. Club Operations & System Maintenance", cls="text-lg font-heading font-bold text-white"),
            cls="flex items-center gap-2.5 mb-1"
        ),
        P("Contact coordinates, weekly meeting schedule, recruitment status, and maintenance mode toggle.", cls="text-xs text-slate-400 mb-5"),
        Div(
            input_field("Official Contact Email", "contact_email", value=cfg.get("contact_email")),
            input_field("Weekly Meeting Schedule & Venue", "meeting_schedule", value=cfg.get("meeting_schedule")),
            cls="grid grid-cols-1 md:grid-cols-2 gap-4"
        ),
        input_field("Recruitment Portal Status", "recruitment_status", value=cfg.get("recruitment_status")),
        Div(
            select_field("Portal Maintenance Mode", "maintenance_mode", [
                ("false", "Normal Operation (Portal fully accessible)"),
                ("true", "Maintenance Mode (Display maintenance notice)")
            ], selected=cfg.get("maintenance_mode")),
            input_field("Maintenance Notice Text", "maintenance_message", value=cfg.get("maintenance_message")),
            cls="grid grid-cols-1 md:grid-cols-2 gap-4"
        ),
        cls="mb-8"
    )

    # Save button floating / bottom card
    save_bar = card(
        Div(
            Div(
                Span("Ready to push updates live?", cls="font-semibold text-white block"),
                Span("Changes take effect immediately across all devices without restarting the server.", cls="text-xs text-slate-400"),
                cls="flex-1"
            ),
            btn_primary(icon("save", "text-sm mr-1.5"), "Publish All Updates Live", type="submit", cls="py-3 px-6 text-sm font-bold shadow-xl", loading_text="Publishing Live Changes..."),
            cls="flex flex-col sm:flex-row sm:items-center justify-between gap-4"
        ),
        cls="sticky bottom-4 z-30 border border-blue-500/30 bg-[#0f172a]/95 backdrop-blur shadow-2xl"
    )

    cms_form = Form(
        sec_identity,
        sec_pillars,
        sec_announcements,
        sec_ops,
        save_bar,
        method="post",
        action="/admin-control/save"
    )

    return page(
        session, u, "Admin Control",
        header,
        alerts_div,
        cms_form
    )

@rt("/admin-control/save", methods=["POST"])
async def admin_control_save_post(session, req: Request):
    u = current_user(session)
    if not u or u["role"] not in ["president", "club_coordinator"]:
        return go("/login")

    form = await req.form()
    form_data = {k: str(v) for k, v in form.items()}
    bulk_update_settings(form_data)
    log_activity(session, "cms_update", "settings", None, f"Admin {u['name']} ({u['role']}) updated website configuration via Admin Control")

    return go("/admin-control?msg=All+website+sections+successfully+updated+live!")

@rt("/admin-control/reset", methods=["POST"])
def admin_control_reset_post(session):
    u = current_user(session)
    if not u or u["role"] not in ["president", "club_coordinator"]:
        return go("/login")

    reset_settings_to_defaults()
    log_activity(session, "cms_reset", "settings", None, f"Admin {u['name']} reset website content to University defaults")

    return go("/admin-control?msg=Website+content+successfully+reset+to+University+defaults.")
