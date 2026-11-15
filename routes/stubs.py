from core import rt, current_user, go
from components import *
SECTIONS = [("/tasks", "Tasks", "Phase 2"), ("/events", "Events", "Phase 3"), ("/files", "Files", "Phase 4"),
            ("/learning", "Learning Hub", "Phase 4"), ("/minutes", "Meeting Minutes", "Phase 5"), ("/finance", "Club Finance", "Phase 5"),
            ("/team", "Core Team", "Phase 6"), ("/join-requests", "Join Requests", "Phase 6"),
            ("/activity", "Activity Logs", "Phase 7"), ("/settings", "Portal Settings", "Phase 7")]
def _make(path, title, phase):
    def stub(session):
        u = current_user(session)
        if not u: return go("/login")
        return page(session, u, title, card(H2(title, cls="font-heading font-bold text-xl"), P(f"This section is built in {phase}.", cls="text-sm text-muted mt-2")))
    stub.__name__ = "stub_" + path.strip("/").replace("-", "_")
    rt(path, methods=["GET"])(stub)
for p, t, ph in SECTIONS: _make(p, t, ph)
