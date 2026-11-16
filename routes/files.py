import os
import uuid
from pathlib import Path
from fasthtml.common import *
from starlette.datastructures import UploadFile
from core import rt, current_user, go, supabase
from components import *
from auth import RANKS, can, log_activity
from cache import get_cached, set_cached, invalidate_cache

FOLDERS = ["General", "Circulars", "Documents", "Minutes", "Finance", "Event Assets", "Learning", "Media"]

def format_bytes(size):
    try:
        b = float(size or 0)
        if b >= 1024 * 1024:
            return f"{b / (1024 * 1024):.1f} MB"
        elif b >= 1024:
            return f"{b / 1024:.1f} KB"
        return f"{int(b)} Bytes"
    except Exception:
        return "Unknown size"

@rt("/files", methods=["GET"])
def files_get(session, folder: str = "all", msg: str = "", error: str = ""):
    u = current_user(session)
    if not u:
        return go("/login")
    role = session.get("view_as") or u["role"]
    rank = RANKS.get(role, 1)

    files = get_cached("files_list", ttl=20)
    if files is None:
        try:
            files = supabase.table("files").select("*, uploader_member:uploader(name, roll)").order("created_at", desc=True).execute().data or []
            set_cached("files_list", files)
        except Exception as e:
            print("Error fetching files:", e)
            files = []

    total_bytes = sum(f.get("size") or 0 for f in files)
    active_files = [f for f in files if folder == "all" or f.get("folder") == folder]

    def file_row(f):
        fid = f["id"]
        uploader_name = f.get("uploader_member", {}).get("name") if f.get("uploader_member") else "Member"
        can_delete = (f.get("uploader") == u["id"] or rank >= 4) and not session.get("view_as")
        link = f.get("link_url") or f.get("path") or "#"
        size_str = format_bytes(f.get("size"))
        is_cloud = "supabase.co" in (link or "") or f.get("size")

        delete_btn = Form(
            btn_ghost(icon("delete", "text-red-400 text-sm"), type="submit", cls="p-1.5 hover:bg-red-500/10 border-0"),
            method="post", action=f"/files/{fid}/delete",
            onsubmit="return confirm('Permanently delete this file from the cloud repository?');",
            cls="inline-block"
        ) if can_delete else ""

        mime = (f.get("mime") or "").lower()
        ic = "description"
        if "pdf" in mime or (f.get("name") or "").endswith(".pdf"):
            ic = "picture_as_pdf"
        elif "image" in mime or any((f.get("name") or "").endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]):
            ic = "image"
        elif "zip" in mime or (f.get("name") or "").endswith(".zip"):
            ic = "folder_zip"
        elif "audio" in mime or "video" in mime:
            ic = "video_file"

        return Div(
            Div(
                Div(icon(ic, "text-blue-400 text-2xl"), cls="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center shrink-0 mr-3.5"),
                Div(
                    H4(f.get("name", "Document"), cls="font-semibold text-sm leading-snug text-white"),
                    Div(
                        Span(f"Folder: {f.get('folder', 'General')}", cls="text-xs text-slate-400 font-mono"),
                        Span("•", cls="text-slate-600 mx-1.5"),
                        Span(size_str, cls="text-xs text-emerald-400 font-mono font-medium"),
                        Span("•", cls="text-slate-600 mx-1.5"),
                        Span(f"By {uploader_name} on {(f.get('created_at') or '')[:10]}", cls="text-xs text-slate-400 font-mono"),
                        cls="flex flex-wrap items-center mt-1"
                    ),
                    cls="truncate flex-1 min-w-0"
                ),
                cls="flex items-center min-w-0 flex-1"
            ),
            Div(
                badge("SUPABASE CLOUD" if is_cloud else "EXTERNAL", "primary" if is_cloud else "secondary"),
                A(
                    btn_primary(icon("download", "text-xs mr-1"), "Download", cls="text-xs py-1.5 px-3 font-semibold"),
                    href=link,
                    target="_blank",
                    download=""
                ) if link and link != "#" else "",
                delete_btn,
                cls="flex items-center gap-2.5 shrink-0"
            ),
            cls="flex items-center justify-between p-3.5 rounded-xl bg-white/[0.02] hover:bg-white/[0.06] border border-white/[0.05] hover:border-blue-500/30 transition-all"
        )

    # Cloud File Upload Modal
    upload_modal = Div(
        Div(onclick="document.getElementById('cloud-upload-modal').classList.add('hidden')", cls="absolute inset-0 bg-black/70 backdrop-blur-sm"),
        card(
            Div(
                Div(
                    H3("Upload to Supabase Cloud Storage", cls="font-heading font-bold text-xl text-white"),
                    P("Files are stored directly in the official Supabase 'club-files' bucket.", cls="text-xs text-slate-400 mt-0.5"),
                    cls="flex-1"
                ),
                Button(icon("close"), onclick="document.getElementById('cloud-upload-modal').classList.add('hidden')", type="button", cls="text-slate-400 hover:text-white bg-transparent border-0 cursor-pointer text-xl"),
                cls="flex items-start justify-between mb-5"
            ),
            Form(
                Div(
                    Label("Select Local File", cls="block text-xs font-mono text-slate-400 mb-1.5"),
                    Input(type="file", name="upload_file", required=True, cls="input w-full file:mr-4 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-500 cursor-pointer"),
                    cls="mb-4"
                ),
                select_field("Target Cloud Folder", "folder", [(f, f) for f in FOLDERS]),
                input_field("Custom Display Name (Optional)", "custom_name", placeholder="Leave blank to keep original filename", required=False),
                Div(
                    btn_ghost("Cancel", type="button", onclick="document.getElementById('cloud-upload-modal').classList.add('hidden')"),
                    btn_primary(icon("cloud_upload", "text-sm mr-1"), "Upload to Supabase Cloud", type="submit", loading_text="Uploading to Cloud..."),
                    cls="flex justify-end gap-3 mt-6 pt-4 border-t border-white/[0.08]"
                ),
                method="post",
                action="/files/upload",
                enctype="multipart/form-data"
            ),
            cls="relative z-10 w-full max-w-lg mx-auto mt-20 border border-blue-500/25 bg-[#0f172a] shadow-2xl"
        ),
        id="cloud-upload-modal",
        cls="fixed inset-0 z-50 flex items-center justify-center p-4 hidden"
    )

    # External Link Modal
    link_modal = Div(
        Div(onclick="document.getElementById('link-modal').classList.add('hidden')", cls="absolute inset-0 bg-black/70 backdrop-blur-sm"),
        card(
            Div(
                H3("Add External Cloud Link", cls="font-heading font-bold text-xl text-white"),
                Button(icon("close"), onclick="document.getElementById('link-modal').classList.add('hidden')", type="button", cls="text-slate-400 hover:text-white bg-transparent border-0 cursor-pointer"),
                cls="flex items-center justify-between mb-4"
            ),
            Form(
                input_field("Document / Resource Name", "name", placeholder="e.g. Annual Hackathon Design Assets"),
                select_field("Target Folder", "folder", [(f, f) for f in FOLDERS]),
                input_field("Resource URL (Google Drive / GitHub / OneDrive)", "link_url", placeholder="https://drive.google.com/..."),
                Div(
                    btn_ghost("Cancel", type="button", onclick="document.getElementById('link-modal').classList.add('hidden')"),
                    btn_primary("Save Link", type="submit"),
                    cls="flex justify-end gap-3 mt-6"
                ),
                method="post",
                action="/files/new"
            ),
            cls="relative z-10 w-full max-w-lg mx-auto mt-20"
        ),
        id="link-modal",
        cls="fixed inset-0 z-50 flex items-center justify-center p-4 hidden"
    )

    # Hero / Header
    header = card(
        Div(
            Div(
                Div(
                    Span("SUPABASE CLOUD STORAGE", cls="text-[11px] font-mono font-bold tracking-wider text-blue-400 uppercase bg-blue-500/10 border border-blue-500/25 px-3 py-1 rounded-full inline-block mb-2"),
                    H1("Cloud File Repository", cls="text-2xl md:text-3xl font-heading font-bold text-white"),
                    P("Central cloud asset repository, committee circulars, event decks, code archives, and design assets.", cls="text-slate-300 text-sm mt-1"),
                    cls="space-y-1"
                ),
                Div(
                    btn_primary(
                        icon("cloud_upload", "text-sm mr-1.5"), "Upload File to Cloud",
                        onclick="document.getElementById('cloud-upload-modal').classList.remove('hidden')",
                        type="button",
                        cls="py-2.5 px-4 text-xs font-semibold shadow-lg shadow-blue-600/30"
                    ),
                    btn_ghost(
                        icon("link", "text-sm mr-1.5"), "Add External Link",
                        onclick="document.getElementById('link-modal').classList.remove('hidden')",
                        type="button",
                        cls="py-2.5 px-4 text-xs font-semibold"
                    ),
                    cls="flex flex-wrap items-center gap-2 mt-4 md:mt-0"
                ),
                cls="flex flex-col md:flex-row md:items-center justify-between gap-4"
            ),
            cls="relative z-10"
        ),
        cls="relative overflow-hidden mb-8 border border-blue-500/20 bg-gradient-to-br from-[#0a1426] via-[#0d1a36] to-[#070d1e]"
    )

    alerts = (
        Div(msg, cls="bg-emerald-900/40 border border-emerald-500/30 p-4 rounded-xl text-emerald-200 text-sm mb-6") if msg else
        (Div(error, cls="bg-red-900/40 border border-red-500/30 p-4 rounded-xl text-red-200 text-sm mb-6") if error else "")
    )

    stats = Div(
        stat_card("Total Stored Files", len(files), "cloud_queue", "Active in repository"),
        stat_card("Cloud Storage Used", format_bytes(total_bytes), "hard_drive", "Supabase bucket 'club-files'"),
        stat_card("Active Categories", len(FOLDERS), "folder_special", "General to Design & Media"),
        stat_card("Storage Engine", "SUPABASE S3", "verified", "High-availability global CDN"),
        cls="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
    )

    folder_chips = card(
        Div(
            A("All Files", href="/files?folder=all", cls=f"px-3.5 py-1.5 rounded-xl text-xs font-mono font-medium transition-all {'bg-blue-600 text-white font-bold shadow-md shadow-blue-600/20' if folder == 'all' else 'text-slate-400 hover:text-white hover:bg-white/[0.05]'}") ,
            *[A(f, href=f"/files?folder={f}", cls=f"px-3.5 py-1.5 rounded-xl text-xs font-mono font-medium transition-all {'bg-blue-600 text-white font-bold shadow-md shadow-blue-600/20' if folder == f else 'text-slate-400 hover:text-white hover:bg-white/[0.05]'}") for f in FOLDERS],
            cls="flex items-center gap-1.5 overflow-x-auto pb-1"
        ),
        p="p-3 mb-6"
    )

    file_list = card(
        Div(
            H3(f"Stored Documents & Assets ({len(active_files)})", cls="font-heading font-semibold text-lg text-white"),
            Span(f"Viewing: {folder.upper()}", cls="text-xs font-mono text-slate-400"),
            cls="flex items-center justify-between mb-4"
        ),
        Div(
            *[file_row(f) for f in active_files] or [
                Div(
                    icon("cloud_off", "text-4xl text-slate-500 mb-2"),
                    P("No files stored in this folder yet. Click 'Upload File to Cloud' above to add documents.", cls="text-slate-400 text-sm text-center font-mono"),
                    cls="text-center py-12"
                )
            ],
            cls="space-y-2.5"
        )
    )

    return page(session, u, "Files", header, alerts, stats, folder_chips, file_list, upload_modal, link_modal)

@rt("/files/upload", methods=["POST"])
async def files_upload_post(session, folder: str, upload_file: UploadFile, custom_name: str = ""):
    u = current_user(session)
    if not u or session.get("view_as"):
        return go("/login")

    if not upload_file or not upload_file.filename:
        return go("/files?error=No+file+was+selected+for+upload.")

    try:
        contents = await upload_file.read()
    except Exception as e:
        return go(f"/files?error=Could+not+read+file:+{str(e)[:50]}")

    if not contents:
        return go("/files?error=Uploaded+file+is+empty.")

    original_name = Path(upload_file.filename).name
    display_name = custom_name.strip() if custom_name and custom_name.strip() else original_name
    ext = Path(original_name).suffix
    storage_path = f"{folder.lower().replace(' ', '_')}/{uuid.uuid4().hex[:8]}_{original_name}"
    content_type = upload_file.content_type or "application/octet-stream"

    # Upload to Supabase Storage bucket 'club-files'
    try:
        supabase.storage.from_("club-files").upload(
            storage_path,
            contents,
            {"content-type": content_type, "upsert": "true"}
        )
        pub_url = supabase.storage.from_("club-files").get_public_url(storage_path)
    except Exception as e:
        print("Supabase cloud upload failed:", e)
        return go(f"/files?error=Supabase+storage+error:+{str(e)[:80]}")

    # Record in files table
    try:
        res = supabase.table("files").insert({
            "name": display_name,
            "folder": folder,
            "path": storage_path,
            "link_url": pub_url,
            "size": len(contents),
            "mime": content_type,
            "uploader": u["id"]
        }).execute()

        if res.data:
            invalidate_cache("files_")
            log_activity(session, "cloud_file_upload", "files", res.data[0]["id"], f"Uploaded '{display_name}' ({format_bytes(len(contents))}) to Supabase Cloud")
    except Exception as e:
        print("Files table record insertion failed:", e)

    return go(f"/files?msg=File+'{display_name}'+successfully+stored+in+Supabase+Cloud+Storage!")

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
            invalidate_cache("files_")
            log_activity(session, "file_added", "files", res.data[0]["id"], f"Added document: {name.strip()} ({folder})")
    except Exception as e:
        print("File addition error:", e)

    return go("/files?msg=External+link+successfully+saved!")

@rt("/files/{fid}/delete", methods=["POST"])
def files_delete_post(session, fid: int):
    u = current_user(session)
    if not u or session.get("view_as"):
        return go("/login")

    try:
        f = supabase.table("files").select("path, link_url").eq("id", fid).limit(1).execute().data
        if f and f[0].get("path") and not f[0]["path"].startswith("http"):
            try:
                supabase.storage.from_("club-files").remove([f[0]["path"]])
            except Exception as e:
                print("Notice: could not delete from storage bucket:", e)
        supabase.table("files").delete().eq("id", fid).execute()
        invalidate_cache("files_")
        log_activity(session, "file_deleted", "files", fid, "Deleted document")
    except Exception as e:
        print("File delete error:", e)

    return go("/files?msg=File+entry+successfully+deleted.")
