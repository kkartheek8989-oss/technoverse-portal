from fasthtml.common import *
from core import rt, current_user, go, supabase
from components import *
from auth import RANKS, can, log_activity

FOLDERS = ["General", "Minutes", "Finance", "Events", "Design", "Learning", "Documentation"]

@rt("/files", methods=["GET"])
def files_get(session, folder: str = "all"):
    u = current_user(session)
    if not u:
        return go("/login")
    role = session.get("view_as") or u["role"]
    rank = RANKS.get(role, 1)

    try:
        files = supabase.table("files").select("*, uploader_member:uploader(name, roll)").order("created_at", desc=True).execute().data or []
    except Exception:
        files = []

    if folder != "all":
        files = [f for f in files if f.get("folder") == folder]

    def file_row(f):
        fid = f["id"]
        uploader_name = f.get("uploader_member", {}).get("name") if f.get("uploader_member") else "Member"
        can_delete = (f.get("uploader") == u["id"] or rank >= 4) and not session.get("view_as")
        link = f.get("link_url") or f.get("path") or "#"

        delete_btn = Form(
            btn_ghost(icon("delete", "text-red-400 text-sm"), type="submit", cls="p-1 hover:bg-red-500/10 border-0"),
            method="post", action=f"/files/{fid}/delete",
            onsubmit="return confirm('Delete this file record?');",
            cls="inline-block"
        ) if can_delete else ""

        return Div(
            Div(
                icon("description", "text-primary text-2xl mr-3 shrink-0"),
                Div(
                    H4(f.get("name", "Document"), cls="font-semibold text-sm leading-snug"),
                    P(f"Folder: {f.get('folder', 'General')} • Added by {uploader_name} on {(f.get('created_at') or '')[:10]}", cls="text-xs text-muted font-mono"),
                    cls="truncate"
                ),
                cls="flex items-center min-w-0 flex-1"
            ),
            Div(
                badge(f.get("folder", "General"), "secondary"),
                A(
                    btn_primary("Open Link", icon("open_in_new", "text-xs"), cls="text-xs py-1.5 px-3"),
                    href=link,
                    target="_blank" if link.startswith("http") else "_self"
                ) if link and link != "#" else "",
                delete_btn,
                cls="flex items-center gap-3"
            ),
            cls="flex items-center justify-between p-3.5 rounded-xl bg-white/5 hover:bg-white/10 transition-colors"
        )

    modal = Div(
        Div(onclick="document.getElementById('file-modal').classList.add('hidden')", cls="absolute inset-0 bg-black/60 backdrop-blur-sm"),
        card(
            Div(
                H3("Add File or Asset Link", cls="font-heading font-bold text-xl"),
                Button(icon("close"), onclick="document.getElementById('file-modal').classList.add('hidden')", type="button", cls="text-muted hover:text-white bg-transparent border-0 cursor-pointer"),
                cls="flex items-center justify-between mb-4"
            ),
            Form(
                input_field("Document / Asset Name", "name", placeholder="e.g. CodeX 2026 Sponsorship Brochure", required=True),
                select_field("Target Folder", "folder", [(f, f) for f in FOLDERS]),
                input_field("Document URL / Drive Link", "link_url", placeholder="https://drive.google.com/... or cloud link", required=True),
                Div(
                    btn_ghost("Cancel", type="button", onclick="document.getElementById('file-modal').classList.add('hidden')"),
                    btn_primary("Save File Entry", type="submit"),
                    cls="flex justify-end gap-3 mt-6"
                ),
                method="post",
                action="/files/new"
            ),
            cls="relative z-10 w-full max-w-lg mx-auto mt-16"
        ),
        id="file-modal",
        cls="fixed inset-0 z-50 flex items-center justify-center p-4 hidden"
    )

    header = Div(
        Div(
            H1("File Repository", cls="font-heading font-bold text-2xl"),
            P("Central asset directory, brand files, event decks, and governance documents", cls="text-sm text-secondary"),
            cls="flex-1"
        ),
        Div(
            btn_primary(
                icon("cloud_upload", "text-sm"), "Add Document Link",
                onclick="document.getElementById('file-modal').classList.remove('hidden')",
                type="button"
            ) if not session.get("view_as") else "",
            cls="flex items-center gap-3"
        ),
        cls="flex flex-wrap items-center justify-between gap-4 mb-6"
    )

    folder_chips = card(
        Div(
            A("All Files", href="/files?folder=all", cls=f"px-3 py-1.5 rounded-lg text-xs font-mono font-medium {'bg-primary text-white' if folder == 'all' else 'text-muted hover:bg-white/5'}"),
            *[A(f, href=f"/files?folder={f}", cls=f"px-3 py-1.5 rounded-lg text-xs font-mono font-medium {'bg-primary text-white' if folder == f else 'text-muted hover:bg-white/5'}") for f in FOLDERS],
            cls="flex items-center gap-1 overflow-x-auto pb-1"
        ),
        p="p-3 mb-6"
    )

    file_list = card(
        H3("Stored Documents & Assets", cls="font-heading font-semibold text-lg mb-4"),
        Div(
            *[file_row(f) for f in files] or [
                Div(P("No files stored in this folder yet.", cls="text-muted text-sm text-center py-12"))
            ],
            cls="space-y-2"
        )
    )

    return page(session, u, "Files", header, folder_chips, file_list, modal)

@rt("/files/new", methods=["POST"])
def files_new_post(session, name: str, folder: str, link_url: str):
    u = current_user(session)
    if not u or session.get("view_as"):
        return go("/login")

    payload = {
        "name": name.strip(),
        "folder": folder,
        "path": link_url.strip(),
        "link_url": link_url.strip(),
        "uploader": u["id"]
    }

    try:
        res = supabase.table("files").insert(payload).execute()
        if res.data:
            log_activity(session, "file_added", "files", res.data[0]["id"], f"Added document: {name.strip()} ({folder})")
    except Exception as e:
        print("File addition error:", e)

    return go("/files")

@rt("/files/{fid}/delete", methods=["POST"])
def files_delete_post(session, fid: int):
    u = current_user(session)
    if not u or session.get("view_as"):
        return go("/login")

    try:
        supabase.table("files").delete().eq("id", fid).execute()
        log_activity(session, "file_deleted", "files", fid, "Deleted document")
    except Exception as e:
        print("File delete error:", e)

    return go("/files")
