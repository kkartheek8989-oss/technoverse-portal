from fasthtml.common import *
from auth import RANKS

def icon(n, cls=""): return Span(n, cls=f"material-symbols-outlined {cls}")
def _cls(base, kw): return f"{base} {kw.pop('cls', '')}".strip()

def btn(*c, **kw):
    base = "inline-flex items-center justify-center gap-2 rounded-lg border text-sm font-medium transition-colors disabled:opacity-50"
    return Button(*c, cls=_cls(base, kw), **kw)
def btn_primary(*c, **kw): return btn(*c, cls=_cls("bg-primary text-white hover:opacity-90 border-transparent px-4 py-2", kw), **kw)
def btn_ghost(*c, **kw): return btn(*c, cls=_cls("border-white/10 text-secondary hover:bg-white/5 px-4 py-2", kw), **kw)
def btn_danger(*c, **kw): return btn(*c, cls=_cls("bg-red-600 text-white border-transparent px-4 py-2", kw), **kw)

BADGES = {"primary": "bg-primary text-white", "secondary": "bg-white/5 text-secondary border border-white/10",
          "amber": "bg-amber text-dark", "done": "bg-emerald-600 text-white", "urgent": "bg-red-500 text-white"}
def badge(text, variant="secondary"):
    return Span(text, cls=f"inline-flex items-center px-2 py-0.5 rounded-full text-xs font-mono {BADGES.get(variant, BADGES['secondary'])}")

def input_field(label, name, type="text", placeholder="", value="", required=True):
    return Div(Label(label, cls="block text-xs font-mono text-muted mb-1"),
               Input(name=name, type=type, placeholder=placeholder, value=value, required=required, cls="input w-full"), cls="mb-4")

def card(*c, cls="", p="p-5"): return Div(*c, cls=f"card rounded-2xl {p} {cls}")

def avatar(name="?", cls="w-8 h-8"):
    ini = "".join(w[0] for w in (name or "?").split()[:2]).upper()
    return Div(ini, cls=f"{cls} rounded-full bg-primary/20 text-primary font-mono text-xs flex items-center justify-center")

NAV = [("Dashboard", "/", "dashboard", 1), ("Tasks", "/tasks", "checklist", 1), ("Events", "/events", "calendar_today", 1),
       ("Files", "/files", "folder", 1), ("Learning Hub", "/learning", "school", 1), ("Meeting Minutes", "/minutes", "description", 3),
       ("Club Finance", "/finance", "account_balance_wallet", 3), ("Core Team", "/team", "groups", 1),
       ("Activity Logs", "/activity", "history", 4), ("Portal Settings", "/settings", "settings", 1)]

def _link(label, url, ic, cls="px-3 py-2 text-sm text-secondary hover:bg-white/5 rounded-lg"):
    return A(icon(ic, "text-muted"), Span(label), href=url, cls=f"flex items-center gap-3 {cls}")

def toast(text, variant="info"):
    col = {"info": "bg-primary", "success": "bg-emerald-600", "error": "bg-red-600"}.get(variant, "bg-primary")
    return Div(text, cls=f"{col} text-white px-4 py-3 rounded-lg shadow-lg text-sm", onclick="this.remove()")

def page(session, user, title, *content):
    real = user["role"]; role = session.get("view_as") or real
    rank = RANKS.get(role, 1); items = [n for n in NAV if rank >= n[3]]
    banner = Div(Span(f"Viewing as: {role.replace('_', ' ').title()} (read-only preview)"),
                 Form(btn("Exit Preview", cls="bg-dark text-amber border-amber px-2 py-1 text-xs"), method="post", action="/view-as/reset"),
                 cls="bg-amber text-dark px-4 py-2 flex items-center justify-between text-xs font-mono") if session.get("view_as") else ""
    top = Div(Div(Div(Img(src="/logo-mark.png", cls="w-9 h-9 rounded-lg bg-white p-1", alt="Technoverse Club logo"),
                      Span("Technoverse", cls="font-heading font-bold text-lg"), cls="flex items-center gap-2"),
                  Div(badge(f"{real.replace('_', ' ').upper()} R{RANKS.get(real, 1)}", "amber" if real == "club_coordinator" else "primary"),
                      avatar(user["name"]), A(icon("logout"), href="/logout", cls="text-muted"), cls="flex items-center gap-3"),
                  cls="flex items-center justify-between px-4 py-3"),
              cls="sticky top-0 z-20 border-b border-white/5 bg-dark/90 backdrop-blur")
    side = Aside(*[_link(l, u, i) for l, u, i, _ in items], cls="hidden md:block w-60 shrink-0 border-r border-white/5 p-4 space-y-1 min-h-screen")
    more = Div(Div(onclick="this.parentElement.classList.add('hidden')", cls="absolute inset-0 bg-black/50"),
               Div(H3("More", cls="font-heading font-bold mb-3"), *[_link(l, u, i) for l, u, i, _ in items[4:]],
                   cls="absolute bottom-0 inset-x-0 card rounded-t-3xl p-5 pb-8"), id="more-sheet", cls="fixed inset-0 z-50 hidden md:hidden")
    bottom = Nav(*[A(icon(i), Span(l.split()[0], cls="text-[10px]"), href=u, cls="flex flex-col items-center px-3 py-1 text-secondary")
                   for l, u, i, _ in items[:4]],
                 Button(icon("more_horiz"), Span("More", cls="text-[10px]"), onclick="document.getElementById('more-sheet').classList.remove('hidden')",
                        cls="flex flex-col items-center px-3 py-1 text-secondary"),
                 cls="md:hidden fixed bottom-0 inset-x-0 z-40 flex justify-around border-t border-white/10 bg-dark/95 py-2")
    return (Title(f"{title} | Technoverse"), banner, top,
            Div(side, Main(*content, id="main", cls="flex-1 min-w-0 p-4 md:p-8 pb-24"), cls="flex"), more, bottom)
