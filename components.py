from fasthtml.common import *
from auth import RANKS

def icon(n, cls=""):
    return Span(n, cls=f"material-symbols-outlined {cls}")

def _cls(base, kw):
    return f"{base} {kw.pop('cls', '')}".strip()

def btn(*c, **kw):
    base = "inline-flex items-center justify-center gap-2 rounded-xl text-sm font-semibold transition-all duration-200 ease-out cursor-pointer disabled:opacity-50 active:scale-95"
    return Button(*c, cls=_cls(base, kw), **kw)

def btn_primary(*c, **kw):
    return btn(*c, cls=_cls("bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-600/25 hover:shadow-blue-600/35 border border-blue-400/20 px-4 py-2", kw), **kw)

def btn_ghost(*c, **kw):
    return btn(*c, cls=_cls("border border-white/10 bg-white/[0.03] hover:bg-white/[0.08] hover:border-white/20 text-slate-300 hover:text-white px-4 py-2", kw), **kw)

def btn_danger(*c, **kw):
    return btn(*c, cls=_cls("bg-red-600/90 hover:bg-red-600 text-white shadow-lg shadow-red-600/20 border border-red-500/20 px-4 py-2", kw), **kw)

def btn_success(*c, **kw):
    return btn(*c, cls=_cls("bg-emerald-600/90 hover:bg-emerald-600 text-white shadow-lg shadow-emerald-600/20 border border-emerald-500/20 px-4 py-2", kw), **kw)

BADGES = {
    "primary": "bg-blue-500/15 text-blue-400 border border-blue-500/30",
    "secondary": "bg-white/5 text-slate-400 border border-white/10",
    "amber": "bg-amber-500/15 text-amber-400 border border-amber-500/30 font-semibold",
    "done": "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30",
    "doing": "bg-blue-500/15 text-blue-400 border border-blue-500/30",
    "todo": "bg-slate-500/15 text-slate-300 border border-slate-500/30",
    "urgent": "bg-red-500/15 text-red-400 border border-red-500/30 font-semibold",
    "high": "bg-orange-500/15 text-orange-400 border border-orange-500/30",
    "medium": "bg-amber-500/15 text-amber-400 border border-amber-500/30",
    "low": "bg-slate-500/15 text-slate-400 border border-slate-500/30",
    "approved": "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-semibold",
    "pending": "bg-amber-500/15 text-amber-400 border border-amber-500/30",
    "rejected": "bg-red-500/15 text-red-400 border border-red-500/30",
    "registered": "bg-blue-500/15 text-blue-400 border border-blue-500/30",
    "waitlist": "bg-amber-500/15 text-amber-400 border border-amber-500/30"
}

def badge(text, variant="secondary"):
    return Span(str(text), cls=f"inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-mono {BADGES.get(variant, BADGES['secondary'])}")

def input_field(label, name, type="text", placeholder="", value="", required=True):
    return Div(
        Label(label, cls="block text-xs font-mono text-slate-400 mb-1.5"),
        Input(name=name, type=type, placeholder=placeholder, value=str(value or ""), required=required, cls="input w-full"),
        cls="mb-4"
    )

def textarea_field(label, name, placeholder="", value="", rows=3, required=False):
    return Div(
        Label(label, cls="block text-xs font-mono text-slate-400 mb-1.5"),
        Textarea(str(value or ""), name=name, placeholder=placeholder, rows=rows, required=required, cls="input w-full resize-y"),
        cls="mb-4"
    )

def select_field(label, name, options, selected=None, required=True):
    opts = []
    for opt in options:
        if isinstance(opt, tuple):
            val, lab = opt
        else:
            val = lab = opt
        is_sel = str(val) == str(selected)
        opts.append(Option(lab, value=str(val), selected=is_sel))
    return Div(
        Label(label, cls="block text-xs font-mono text-slate-400 mb-1.5"),
        Select(*opts, name=name, required=required, cls="input w-full bg-[#0b1120]"),
        cls="mb-4"
    )

def card(*c, cls="", p="p-6"):
    return Div(*c, cls=f"card {p} {cls}")

def stat_card(label, value, ic="analytics", subtext=""):
    return card(
        Div(
            Div(label, cls="text-xs text-slate-400 font-mono tracking-wider uppercase font-semibold"),
            Div(icon(ic, "text-blue-400 text-lg"), cls="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center") if ic else "",
            cls="flex items-center justify-between"
        ),
        Div(str(value), cls="text-2xl sm:text-3xl font-mono font-bold text-white mt-3"),
        Div(subtext, cls="text-[11px] text-slate-400 mt-1 font-mono") if subtext else ""
    )

def avatar(name="?", cls="w-8 h-8"):
    words = (name or "?").strip().split()
    ini = ("".join(w[0] for w in words[:2]) if words else "?").upper()
    return Div(ini, cls=f"{cls} rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 text-white font-mono text-xs flex items-center justify-center font-bold shrink-0 shadow-sm border border-white/20")

def format_inr(amount):
    try:
        val = int(float(amount or 0))
        s = str(val)
        if len(s) <= 3:
            return f"₹{s}"
        last3 = s[-3:]
        rem = s[:-3]
        groups = []
        while len(rem) > 2:
            groups.insert(0, rem[-2:])
            rem = rem[:-2]
        if rem:
            groups.insert(0, rem)
        return f"₹{','.join(groups)},{last3}"
    except Exception:
        return f"₹{amount}"

def hari_university_badge(cls=""):
    return Div(
        Img(src="/hari-university-logo.png", alt="Hari University Official Seal", cls="w-8 h-8 object-contain shrink-0 drop-shadow"),
        Div(
            Span("Hari University", cls="font-heading font-bold text-xs leading-none text-white block"),
            Span("Affiliated Campus", cls="text-[9px] text-amber-400 font-mono font-medium leading-none block mt-0.5"),
            cls="hidden sm:block text-left"
        ),
        cls=f"flex items-center gap-2.5 bg-white/[0.04] hover:bg-white/[0.08] border border-white/10 px-3 py-1.5 rounded-xl transition-all {cls}"
    )

def footer():
    return Footer(
        Div(
            Div(
                Span("Built by Technoverse.", cls="font-bold text-white"),
                Span(" All rights reserved.", cls="text-slate-400 ml-1"),
                cls="text-xs font-mono"
            ),
            Div(
                Span("Technoverse Club • Official Technical Body of Hari University", cls="text-[11px] text-slate-400 font-mono"),
                cls="text-center sm:text-right"
            ),
            cls="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 px-4 py-8 border-t border-white/[0.07] mt-16 text-center sm:text-left"
        )
    )

NAV = [
    ("Dashboard", "/", "dashboard", 1),
    ("Tasks", "/tasks", "checklist", 1),
    ("Events", "/events", "calendar_today", 1),
    ("Files", "/files", "folder", 1),
    ("Learning Hub", "/learning", "school", 1),
    ("Meeting Minutes", "/minutes", "description", 3),
    ("Club Finance", "/finance", "account_balance_wallet", 3),
    ("Core Team", "/team", "groups", 1),
    ("Join Requests", "/join-requests", "person_add", 4),
    ("Activity Logs", "/activity", "history", 4),
    ("Portal Settings", "/settings", "settings", 1)
]

def _link(label, url, ic, cls="px-3.5 py-2.5 text-sm font-medium text-slate-300 hover:text-white hover:bg-white/[0.06] rounded-xl transition-all duration-150"):
    return A(icon(ic, "text-slate-400 group-hover:text-blue-400 text-lg"), Span(label), href=url, cls=f"group flex items-center gap-3 {cls}")

def toast(text, variant="info"):
    col = {"info": "bg-blue-600", "success": "bg-emerald-600", "error": "bg-red-600"}.get(variant, "bg-blue-600")
    return Div(text, cls=f"{col} text-white px-4 py-3 rounded-xl shadow-2xl text-sm fixed top-4 right-4 z-50 transition-all font-medium", onclick="this.remove()")

def page(session, user, title, *content):
    real = user["role"]
    role = session.get("view_as") or real
    rank = RANKS.get(role, 1)
    items = [n for n in NAV if rank >= n[3]]

    # Exclusive executive desks for President and Vice President
    if role in ["president", "club_coordinator"]:
        items.insert(1, ("President Desk", "/president", "gavel", 4))
    if role in ["vice_president", "club_coordinator"]:
        idx = 2 if role == "club_coordinator" else 1
        items.insert(idx, ("VP Operations", "/vice-president", "military_tech", 4))

    banner = Div(
        Span(f"Viewing as: {role.replace('_', ' ').title()} (read-only preview)"),
        Form(btn("Exit Preview", cls="bg-dark text-amber border-amber px-2.5 py-1 text-xs"), method="post", action="/view-as/reset"),
        cls="bg-amber-500/90 text-slate-950 px-4 py-2 flex items-center justify-between text-xs font-mono font-bold sticky top-0 z-30 shadow-md"
    ) if session.get("view_as") else ""

    top = Div(
        Div(
            Div(
                Img(src="/logo-mark.png", cls="w-9 h-9 rounded-xl bg-white p-1 shadow-md", alt="Technoverse Club logo"),
                Span("Technoverse", cls="font-heading font-bold text-lg hidden sm:inline text-white"),
                cls="flex items-center gap-2.5"
            ),
            Div(
                hari_university_badge(),
                badge(f"{real.replace('_', ' ').upper()} R{RANKS.get(real, 1)}", "amber" if real == "club_coordinator" else "primary"),
                avatar(user["name"]),
                A(icon("logout"), href="/logout", cls="text-slate-400 hover:text-white transition-colors p-1", title="Sign out"),
                cls="flex items-center gap-3"
            ),
            cls="flex items-center justify-between px-6 py-3.5"
        ),
        cls="sticky top-0 z-20 border-b border-white/[0.06] bg-[#080c14]/80 backdrop-blur-xl"
    )

    side = Aside(
        *[_link(l, u, i) for l, u, i, _ in items],
        cls="hidden md:block w-64 shrink-0 border-r border-white/[0.06] p-4 space-y-1.5 min-h-[calc(100vh-65px)] bg-[#080c14]/30"
    )

    more = Div(
        Div(onclick="document.getElementById('more-sheet').classList.add('hidden')", cls="absolute inset-0 bg-black/70 backdrop-blur-sm"),
        Div(
            H3("Enterprise Navigation", cls="font-heading font-bold mb-4 text-lg text-white"),
            *[_link(l, u, i) for l, u, i, _ in items[4:]],
            cls="absolute bottom-0 inset-x-0 card rounded-t-3xl p-6 pb-10 space-y-2 border-t border-white/10 shadow-2xl"
        ),
        id="more-sheet",
        cls="fixed inset-0 z-50 hidden md:hidden"
    )

    bottom = Nav(
        *[A(icon(i), Span(l.split()[0], cls="text-[10px] font-mono"), href=u, cls="flex flex-col items-center px-3 py-1 text-slate-400 hover:text-white transition-colors")
          for l, u, i, _ in items[:4]],
        Button(
            icon("more_horiz"), Span("More", cls="text-[10px] font-mono"),
            onclick="document.getElementById('more-sheet').classList.remove('hidden')",
            type="button",
            cls="flex flex-col items-center px-3 py-1 text-slate-400 hover:text-white border-0 bg-transparent cursor-pointer"
        ),
        cls="md:hidden fixed bottom-0 inset-x-0 z-40 flex justify-around border-t border-white/[0.08] bg-[#080c14]/90 backdrop-blur-xl py-2 shadow-2xl"
    )

    return (
        Title(f"{title} | Technoverse"),
        banner,
        top,
        Div(
            side,
            Main(*content, footer(), id="main", cls="flex-1 min-w-0 p-4 md:p-8 pb-24"),
            cls="flex"
        ),
        more,
        bottom
    )
