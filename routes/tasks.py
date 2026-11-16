from datetime import datetime, timezone
from fasthtml.common import *
from core import rt, current_user, go, supabase
from components import *
from auth import RANKS, can, log_activity
from cache import get_cached, set_cached, invalidate_cache

@rt("/tasks", methods=["GET"])
def tasks_get(session, filter: str = "all", priority: str = "all", sprint: str = "all", edit_id: int = None):
    u = current_user(session)
    if not u:
        return go("/login")
    role = session.get("view_as") or u["role"]
    rank = RANKS.get(role, 1)

    # Fetch tasks (cached 15s)
    tasks = get_cached("tasks_list", ttl=15)
    if tasks is None:
        try:
            tasks = supabase.table("tasks").select("*, assigned:assigned_to(id, name, roll)").order("created_at", desc=True).execute().data or []
            set_cached("tasks_list", tasks)
        except Exception as e:
            print("Tasks fetch error:", e)
            tasks = []

    # Fetch members for assignment dropdown (cached 30s)
    members = get_cached("members_active", ttl=30)
    if members is None:
        try:
            members = supabase.table("members").select("id, name, roll, role").eq("active", True).execute().data or []
            set_cached("members_active", members)
        except Exception:
            members = []

    # Task to edit if edit_id is passed
    task_to_edit = None
    if edit_id:
        for t in tasks:
            if str(t.get("id")) == str(edit_id):
                task_to_edit = t
                break

    # Apply filters
    filtered_tasks = tasks
    if filter == "mine":
        filtered_tasks = [t for t in filtered_tasks if t.get("assigned_to") == u["id"]]
    if priority != "all":
        filtered_tasks = [t for t in filtered_tasks if t.get("priority") == priority]
    if sprint != "all":
        filtered_tasks = [t for t in filtered_tasks if t.get("sprint") == sprint]

    todo_tasks = [t for t in filtered_tasks if t.get("status") == "todo"]
    doing_tasks = [t for t in filtered_tasks if t.get("status") == "doing"]
    done_tasks = [t for t in filtered_tasks if t.get("status") == "done"]

    def task_card(t):
        assigned_name = t.get("assigned", {}).get("name") if t.get("assigned") else "Unassigned"
        can_edit = (rank >= 3 or t.get("assigned_to") == u["id"] or t.get("created_by") == u["id"]) and not session.get("view_as")
        can_delete = (rank >= 4 or t.get("created_by") == u["id"]) and not session.get("view_as")
        due = (t.get("due_at") or "")[:10]
        
        status_opts = [("todo", "To Do"), ("doing", "In Progress"), ("done", "Done")]
        status_form = Form(
            Select(
                *[Option(lab, value=val, selected=(val == t.get("status"))) for val, lab in status_opts],
                name="status",
                onchange="this.form.submit()",
                cls="input text-xs py-1 px-2 font-mono bg-dark"
            ),
            method="post",
            action=f"/tasks/{t['id']}/status",
            cls="inline-block"
        ) if can_edit else badge(t.get("status", "todo").upper(), t.get("status", "todo"))

        edit_btn = A(
            btn_ghost(icon("edit", "text-secondary text-xs"), type="button", cls="p-1 hover:bg-white/10 hover:text-white border-0"),
            href=f"/tasks/{t['id']}/edit",
            title="Edit Task",
            cls="inline-block"
        ) if can_edit else ""

        delete_btn = Form(
            btn_ghost(icon("delete", "text-red-400 text-xs"), type="submit", cls="p-1 hover:bg-red-500/10 border-0"),
            method="post",
            action=f"/tasks/{t['id']}/delete",
            onsubmit="return confirm('Delete this task permanently?');",
            title="Delete Task",
            cls="inline-block"
        ) if can_delete else ""

        return card(
            Div(
                Div(
                    Span(f"#TK-{t.get('code', t.get('id'))}", cls="font-mono text-xs text-muted font-bold"),
                    badge(t.get("priority", "medium").upper(), t.get("priority", "medium")),
                    cls="flex items-center gap-2"
                ),
                Div(
                    edit_btn,
                    delete_btn,
                    cls="flex items-center gap-1"
                ),
                cls="flex items-center justify-between mb-2"
            ),
            H4(t.get("title", ""), cls="font-semibold text-sm mb-1 leading-snug"),
            P(t.get("description", ""), cls="text-xs text-muted mb-3 line-clamp-2") if t.get("description") else "",
            Div(
                Div(
                    avatar(assigned_name, cls="w-6 h-6 text-[10px]"),
                    Span(assigned_name, cls="text-xs text-secondary truncate max-w-[120px]"),
                    cls="flex items-center gap-2"
                ),
                status_form,
                cls="flex items-center justify-between pt-2 border-t border-white/5"
            ),
            Div(
                Span(icon("event", "text-xs mr-1 text-muted"), due, cls="text-[11px] text-muted font-mono flex items-center") if due else "",
                Span(t.get("sprint", ""), cls="text-[10px] font-mono text-primary bg-primary/10 px-2 py-0.5 rounded") if t.get("sprint") else "",
                cls="flex items-center justify-between mt-2"
            ),
            cls="mb-3 hover:border-white/20 transition-all",
            p="p-4"
        )

    def kanban_col(title, count, items, col_badge="secondary"):
        return Div(
            Div(
                Div(
                    H3(title, cls="font-heading font-semibold text-sm"),
                    badge(str(count), col_badge),
                    cls="flex items-center gap-2"
                ),
                cls="flex items-center justify-between mb-4 pb-2 border-b border-white/10"
            ),
            Div(
                *[task_card(t) for t in items] or [
                    Div(P(f"No tasks in {title.lower()}", cls="text-xs text-muted text-center py-8 bg-white/5 rounded-xl border border-dashed border-white/10"))
                ],
                cls="space-y-3 min-h-[300px]"
            ),
            cls="bg-dark/40 border border-white/5 rounded-2xl p-4 flex-1 min-w-[280px]"
        )

    # 1. New Task Modal
    new_task_modal = Div(
        Div(onclick="document.getElementById('task-modal').classList.add('hidden')", cls="absolute inset-0 bg-black/60 backdrop-blur-sm"),
        card(
            Div(
                H3("Create New Task", cls="font-heading font-bold text-xl"),
                Button(icon("close"), onclick="document.getElementById('task-modal').classList.add('hidden')", type="button", cls="text-muted hover:text-white bg-transparent border-0 cursor-pointer"),
                cls="flex items-center justify-between mb-4"
            ),
            Form(
                input_field("Task Title", "title", placeholder="e.g. Set up CI/CD pipeline", required=True),
                textarea_field("Description", "description", placeholder="Provide task context and acceptance criteria...", rows=3),
                Div(
                    select_field("Priority", "priority", [("low", "Low"), ("medium", "Medium"), ("high", "High"), ("urgent", "Urgent")]),
                    select_field("Sprint", "sprint", [("Sprint 1", "Sprint 1"), ("Sprint 2", "Sprint 2"), ("Sprint 3", "Sprint 3"), ("Backlog", "Backlog")]),
                    cls="grid grid-cols-2 gap-3"
                ),
                Div(
                    select_field("Assign To", "assigned_to", [("", "Unassigned")] + [(m["id"], f"{m['name']} ({m['role']})") for m in members], required=False),
                    input_field("Due Date", "due_at", type="date", required=False),
                    cls="grid grid-cols-2 gap-3"
                ),
                Div(
                    btn_ghost("Cancel", type="button", onclick="document.getElementById('task-modal').classList.add('hidden')"),
                    btn_primary("Create Task", type="submit", loading_text="Creating Task..."),
                    cls="flex justify-end gap-3 mt-6"
                ),
                method="post",
                action="/tasks/new"
            ),
            cls="relative z-10 w-full max-w-lg mx-auto mt-16 max-h-[90vh] overflow-y-auto"
        ),
        id="task-modal",
        cls="fixed inset-0 z-50 flex items-center justify-center p-4 hidden"
    )

    # 2. Edit Task Modal (Rendered if editing a task)
    edit_task_modal = ""
    if task_to_edit:
        t_due = (task_to_edit.get("due_at") or "")[:10]
        edit_task_modal = Div(
            A(cls="absolute inset-0 bg-black/60 backdrop-blur-sm", href="/tasks"),
            card(
                Div(
                    Div(
                        H3(f"Edit Task #TK-{task_to_edit.get('code', task_to_edit.get('id'))}", cls="font-heading font-bold text-xl"),
                        P("Update task properties, assignee, and progress state", cls="text-xs text-muted mt-0.5")
                    ),
                    A(icon("close"), href="/tasks", cls="text-muted hover:text-white"),
                    cls="flex items-center justify-between mb-4"
                ),
                Form(
                    input_field("Task Title", "title", value=task_to_edit.get("title", ""), required=True),
                    textarea_field("Description", "description", value=task_to_edit.get("description", "") or "", rows=3),
                    Div(
                        select_field("Status", "status", [("todo", "To Do"), ("doing", "In Progress"), ("done", "Done")], selected=task_to_edit.get("status", "todo")),
                        select_field("Priority", "priority", [("low", "Low"), ("medium", "Medium"), ("high", "High"), ("urgent", "Urgent")], selected=task_to_edit.get("priority", "medium")),
                        cls="grid grid-cols-2 gap-3"
                    ),
                    Div(
                        select_field("Sprint", "sprint", [("Sprint 1", "Sprint 1"), ("Sprint 2", "Sprint 2"), ("Sprint 3", "Sprint 3"), ("Backlog", "Backlog")], selected=task_to_edit.get("sprint", "Sprint 1")),
                        select_field("Assign To", "assigned_to", [("", "Unassigned")] + [(m["id"], f"{m['name']} ({m['role']})") for m in members], selected=task_to_edit.get("assigned_to", ""), required=False),
                        cls="grid grid-cols-2 gap-3"
                    ),
                    input_field("Due Date", "due_at", type="date", value=t_due, required=False),
                    Div(
                        A(btn_ghost("Cancel", type="button"), href="/tasks"),
                        btn_primary("Save Changes", type="submit", loading_text="Saving Changes..."),
                        cls="flex justify-end gap-3 mt-6"
                    ),
                    method="post",
                    action=f"/tasks/{task_to_edit['id']}/edit"
                ),
                cls="relative z-10 w-full max-w-lg mx-auto mt-16 max-h-[90vh] overflow-y-auto"
            ),
            id="edit-modal",
            cls="fixed inset-0 z-50 flex items-center justify-center p-4"
        )

    header = Div(
        Div(
            H1("Task Board", cls="font-heading font-bold text-2xl"),
            P("Track, prioritize, and manage core team deliverables", cls="text-sm text-secondary"),
            cls="flex-1"
        ),
        Div(
            btn_primary(
                icon("add", "text-sm"), "New Task",
                onclick="document.getElementById('task-modal').classList.remove('hidden')",
                type="button"
            ) if rank >= 3 and not session.get("view_as") else "",
            cls="flex items-center gap-3"
        ),
        cls="flex flex-wrap items-center justify-between gap-4 mb-6"
    )

    filters_bar = card(
        Div(
            Div(
                A("All Tasks", href="/tasks?filter=all", cls=f"px-3 py-1.5 rounded-lg text-xs font-mono font-medium {'bg-primary text-white' if filter == 'all' else 'text-muted hover:bg-white/5'}"),
                A("My Tasks", href="/tasks?filter=mine", cls=f"px-3 py-1.5 rounded-lg text-xs font-mono font-medium {'bg-primary text-white' if filter == 'mine' else 'text-muted hover:bg-white/5'}"),
                cls="flex items-center gap-1"
            ),
            Div(
                Form(
                    Select(
                        Option("All Priorities", value="all"),
                        Option("Urgent", value="urgent", selected=(priority == "urgent")),
                        Option("High", value="high", selected=(priority == "high")),
                        Option("Medium", value="medium", selected=(priority == "medium")),
                        Option("Low", value="low", selected=(priority == "low")),
                        name="priority", onchange="this.form.submit()", cls="input text-xs py-1 px-2 font-mono"
                    ),
                    Input(type="hidden", name="filter", value=filter),
                    method="get", action="/tasks", cls="inline-block"
                ),
                cls="flex items-center gap-2"
            ),
            cls="flex flex-wrap items-center justify-between gap-3"
        ),
        p="p-3 mb-6"
    )

    board = Div(
        kanban_col("To Do", len(todo_tasks), todo_tasks, "todo"),
        kanban_col("In Progress", len(doing_tasks), doing_tasks, "doing"),
        kanban_col("Done", len(done_tasks), done_tasks, "done"),
        cls="flex flex-col lg:flex-row gap-6 overflow-x-auto pb-6"
    )

    return page(session, u, "Tasks", header, filters_bar, board, new_task_modal, edit_task_modal)

@rt("/tasks/{tid}/edit", methods=["GET"])
def task_edit_get(session, tid: int):
    return tasks_get(session, edit_id=tid)

@rt("/tasks/{tid}/edit", methods=["POST"])
def task_edit_post(session, tid: int, title: str, description: str = "", status: str = "todo", priority: str = "medium", sprint: str = "", assigned_to: str = "", due_at: str = ""):
    u = current_user(session)
    if not u or session.get("view_as"):
        return go("/login")

    payload = {
        "title": title.strip(),
        "description": description.strip() if description else None,
        "status": status,
        "priority": priority,
        "sprint": sprint.strip() if sprint else None,
        "assigned_to": assigned_to if assigned_to else None,
        "due_at": f"{due_at}T23:59:59Z" if due_at else None
    }

    try:
        res = supabase.table("tasks").update(payload).eq("id", tid).execute()
        invalidate_cache("tasks_")
        invalidate_cache("dashboard_")
        if res.data:
            log_activity(session, "task_edited", "tasks", tid, f"Updated task: {title.strip()}")
    except Exception as e:
        print("Task update failed:", e)

    return go("/tasks")

@rt("/tasks/new", methods=["POST"])
def tasks_new_post(session, title: str, description: str = "", priority: str = "medium", sprint: str = "", assigned_to: str = "", due_at: str = ""):
    u = current_user(session)
    if not u or session.get("view_as"):
        return go("/login")
    if RANKS.get(u["role"], 1) < 3:
        return go("/tasks")

    payload = {
        "title": title.strip(),
        "description": description.strip() if description else None,
        "priority": priority,
        "status": "todo",
        "sprint": sprint.strip() if sprint else None,
        "assigned_to": assigned_to if assigned_to else None,
        "created_by": u["id"],
        "due_at": f"{due_at}T23:59:59Z" if due_at else None
    }

    try:
        res = supabase.table("tasks").insert(payload).execute()
        invalidate_cache("tasks_")
        invalidate_cache("dashboard_")
        if res.data:
            log_activity(session, "task_created", "tasks", res.data[0]["id"], f"Created task: {title.strip()}")
    except Exception as e:
        print("Task creation failed:", e)

    return go("/tasks")

@rt("/tasks/{tid}/status", methods=["POST"])
def task_update_status(session, tid: int, status: str):
    u = current_user(session)
    if not u or session.get("view_as"):
        return go("/login")
    
    if status not in ("todo", "doing", "done"):
        return go("/tasks")

    q = supabase.table("tasks").update({"status": status}).eq("id", tid)
    if RANKS.get(u["role"], 1) < 3:
        q = q.eq("assigned_to", u["id"])
    
    res = q.execute()
    invalidate_cache("tasks_")
    invalidate_cache("dashboard_")
    if res.data:
        log_activity(session, f"task_{status}", "tasks", tid, f"Status updated to {status}: {res.data[0].get('title', '')}")
    return go("/tasks")

@rt("/tasks/{tid}/delete", methods=["POST"])
def task_delete(session, tid: int):
    u = current_user(session)
    if not u or session.get("view_as") or RANKS.get(u["role"], 1) < 4:
        return go("/tasks")

    try:
        supabase.table("tasks").delete().eq("id", tid).execute()
        invalidate_cache("tasks_")
        invalidate_cache("dashboard_")
        log_activity(session, "task_deleted", "tasks", tid, "Deleted task")
    except Exception as e:
        print("Task delete failed:", e)

    return go("/tasks")
