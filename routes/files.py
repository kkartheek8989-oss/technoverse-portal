import os
import uuid
import asyncio
import urllib.parse
from pathlib import Path
from fasthtml.common import *
from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse
from core import rt, current_user, go, supabase
from db import _url
from components import *
from auth import RANKS, can, log_activity
from cache import get_cached, set_cached, invalidate_cache

FOLDERS = ["General", "Circulars", "Documents", "Minutes", "Finance", "Event Assets", "Learning", "Media"]

def ensure_bucket_public():
    """Guarantee that the club-files bucket is permanently marked public."""
    try:
        supabase.storage.update_bucket("club-files", {"public": True})
    except Exception:
        try:
            supabase.storage.create_bucket("club-files", {"public": True})
        except Exception:
            pass

# Guarantee public status on load
try:
    ensure_bucket_public()
except Exception:
    pass

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

    def file_row(f, idx=0):
        fid = f["id"]
        uploader_name = f.get("uploader_member", {}).get("name") if f.get("uploader_member") else "Member"
        can_delete = (f.get("uploader") == u["id"] or rank >= 4) and not session.get("view_as")
        link = f.get("link_url") or f.get("path") or "#"
        size_str = format_bytes(f.get("size"))
        is_cloud = "supabase.co" in (link or "") or f.get("size")

        delete_btn = Form(
            btn_ghost(icon("delete", "text-red-400 text-sm"), type="submit", cls="p-1.5 hover:bg-red-500/10 border-0 rounded-lg transition-colors"),
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

        download_btn = A(
            Span(icon("download", "text-xs mr-1.5 transition-transform group-hover:translate-y-0.5"), cls="shrink-0 dl-icon"),
            Span("Download", cls="dl-text font-semibold"),
            Span(cls="dl-spinner hidden spinner-ring w-3 h-3 border-white/30 border-t-white ml-1.5 shrink-0"),
            href=f"/files/{fid}/download",
            target="_blank",
            onclick="handleFileDownload(this);",
            cls="dl-btn group/btn text-xs py-1.5 px-3 font-semibold rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-md shadow-blue-600/20 hover:shadow-blue-600/40 active:scale-95 transition-all flex items-center cursor-pointer"
        ) if link and link != "#" else ""

        return Div(
            Div(
                Div(icon(ic, "text-blue-400 text-2xl group-hover:text-cyan-300 transition-colors"), cls="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center shrink-0 mr-3.5 group-hover:scale-105 group-hover:bg-blue-500/20 transition-all"),
                Div(
                    H4(f.get("name", "Document"), cls="font-semibold text-sm leading-snug text-white group-hover:text-blue-300 transition-colors truncate"),
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
                download_btn,
                delete_btn,
                cls="flex items-center gap-2.5 shrink-0"
            ),
            style=f"animation-delay: {min(idx * 35, 350)}ms;",
            cls="animate-fade-in flex items-center justify-between p-3.5 rounded-xl bg-white/[0.02] hover:bg-white/[0.05] border border-white/[0.05] hover:border-blue-500/35 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-blue-500/5 group"
        )

    # Cloud File Upload Modal with Real-time Streaming Progress & Dropzone
    upload_script = Script("""
    function updateDropzoneInfo(input) {
        if (input.files && input.files[0]) {
            const f = input.files[0];
            const sz = (f.size / (1024*1024)).toFixed(2);
            document.getElementById('dropzone-text').textContent = f.name;
            document.getElementById('dropzone-sub').textContent = sz + ' MB • ' + (f.type || 'Document');
            const dz = document.getElementById('dropzone-box');
            dz.classList.add('border-emerald-500/60', 'bg-emerald-500/[0.06]');
            dz.classList.remove('border-blue-500/30', 'bg-blue-500/[0.02]');
        }
    }

    let activeCloudXhr = null;

    function cancelCloudUpload() {
        if (activeCloudXhr) {
            activeCloudXhr.abort();
            activeCloudXhr = null;
        }
        const prog = document.getElementById('cloud-upload-progress-container');
        if (prog) prog.classList.add('hidden');
        const sBtn = document.getElementById('cloud-upload-submit-btn');
        if (sBtn) {
            sBtn.disabled = false;
            sBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        }
        document.getElementById('cloud-upload-modal').classList.add('hidden');
    }

    function handleFastCloudUpload(e) {
        e.preventDefault();
        const form = e.target;
        const fileInput = document.getElementById('file-upload-input');
        if (!fileInput || !fileInput.files || !fileInput.files[0]) {
            alert('Please select or drop a file to upload.');
            return false;
        }
        const progressContainer = document.getElementById('cloud-upload-progress-container');
        const progressBar = document.getElementById('cloud-upload-progress-bar');
        const progressPercent = document.getElementById('cloud-upload-percent');
        const progressStatus = document.getElementById('cloud-upload-status');
        const progressSpeed = document.getElementById('cloud-upload-speed');
        const progressBytes = document.getElementById('cloud-upload-bytes');
        const submitBtn = document.getElementById('cloud-upload-submit-btn');
        const errorBox = document.getElementById('cloud-upload-error');

        if (errorBox) errorBox.classList.add('hidden');
        if (progressContainer) progressContainer.classList.remove('hidden');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.classList.add('opacity-50', 'cursor-not-allowed');
        }

        const xhr = new XMLHttpRequest();
        activeCloudXhr = xhr;
        const startTime = Date.now();

        xhr.upload.onprogress = function(evt) {
            if (evt.lengthComputable) {
                const percent = Math.min(99, Math.round((evt.loaded / evt.total) * 100));
                if (progressBar) progressBar.style.width = percent + '%';
                if (progressPercent) progressPercent.textContent = percent + '%';

                const mbLoaded = (evt.loaded / (1024 * 1024)).toFixed(2);
                const mbTotal = (evt.total / (1024 * 1024)).toFixed(2);
                const elapsed = (Date.now() - startTime) / 1000;
                const speed = elapsed > 0.1 ? ((evt.loaded / (1024 * 1024)) / elapsed).toFixed(1) : '0';

                if (progressBytes) progressBytes.textContent = `${mbLoaded} / ${mbTotal} MB`;
                if (progressSpeed) progressSpeed.textContent = `${speed} MB/s`;

                if (percent < 98) {
                    if (progressStatus) progressStatus.textContent = 'Uploading to Server...';
                } else {
                    if (progressStatus) progressStatus.innerHTML = '<span class="inline-block animate-spin mr-1">⚡</span> Storing in Supabase Cloud Bucket...';
                }
            }
        };

        xhr.onload = function() {
            activeCloudXhr = null;
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    const res = JSON.parse(xhr.responseText);
                    if (progressBar) {
                        progressBar.style.width = '100%';
                        progressBar.classList.remove('bg-gradient-to-r', 'from-blue-600', 'to-cyan-400');
                        progressBar.classList.add('bg-emerald-500');
                    }
                    if (progressPercent) progressPercent.textContent = '100%';
                    if (progressStatus) progressStatus.innerHTML = '✓ Stored in Supabase Cloud!';
                    setTimeout(() => {
                        window.location.href = res.redirect || '/files?msg=File+uploaded+successfully';
                    }, 350);
                } catch(err) {
                    window.location.href = '/files?msg=File+stored+in+Supabase+Cloud!';
                }
            } else {
                let errMsg = 'Upload failed. Please check connection and try again.';
                try {
                    const res = JSON.parse(xhr.responseText);
                    if (res.error) errMsg = res.error;
                } catch(e) {}
                if (errorBox) {
                    errorBox.textContent = errMsg;
                    errorBox.classList.remove('hidden');
                }
                if (progressContainer) progressContainer.classList.add('hidden');
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                }
            }
        };

        xhr.onerror = function() {
            activeCloudXhr = null;
            if (errorBox) {
                errorBox.textContent = 'Network error during upload. Please verify connectivity.';
                errorBox.classList.remove('hidden');
            }
            if (progressContainer) progressContainer.classList.add('hidden');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            }
        };

        const formData = new FormData(form);
        xhr.open('POST', form.action, true);
        xhr.setRequestHeader('Accept', 'application/json');
        xhr.send(formData);
        return false;
    }
    """)

    upload_modal = Div(
        Div(onclick="cancelCloudUpload()", cls="absolute inset-0 bg-black/75 backdrop-blur-sm"),
        card(
            Div(
                Div(
                    H3("Upload to Supabase Cloud Storage", cls="font-heading font-bold text-xl text-white"),
                    P("High-speed direct streaming to official 'club-files' Supabase bucket.", cls="text-xs text-slate-400 mt-0.5"),
                    cls="flex-1"
                ),
                Button(icon("close"), onclick="cancelCloudUpload()", type="button", cls="text-slate-400 hover:text-white bg-transparent border-0 cursor-pointer text-xl"),
                cls="flex items-start justify-between mb-5 pb-3 border-b border-white/[0.08]"
            ),
            Div(id="cloud-upload-error", cls="hidden mb-4 p-3 bg-red-950/60 border border-red-500/40 rounded-xl text-xs text-red-200 font-mono"),
            Form(
                # Dropzone File Selector
                Div(
                    Div(
                        icon("cloud_upload", "text-3xl text-blue-400 mb-2 block"),
                        P("Click to browse or drag & drop file here", id="dropzone-text", cls="text-xs font-semibold text-slate-200 truncate px-2"),
                        P("PDF, PNG, JPG, ZIP, DOCX up to 50MB", id="dropzone-sub", cls="text-[11px] text-slate-400 font-mono mt-0.5"),
                        Input(type="file", id="file-upload-input", name="upload_file", required=True, onchange="updateDropzoneInfo(this)", cls="hidden"),
                        id="dropzone-box",
                        onclick="document.getElementById('file-upload-input').click()",
                        ondragover="event.preventDefault(); this.classList.add('border-blue-400', 'bg-blue-500/10');",
                        ondragleave="this.classList.remove('border-blue-400', 'bg-blue-500/10');",
                        ondrop="""event.preventDefault(); this.classList.remove('border-blue-400', 'bg-blue-500/10');
                                if (event.dataTransfer.files && event.dataTransfer.files[0]) {
                                    document.getElementById('file-upload-input').files = event.dataTransfer.files;
                                    updateDropzoneInfo(document.getElementById('file-upload-input'));
                                }""",
                        cls="border-2 border-dashed border-blue-500/30 hover:border-blue-400/60 rounded-xl p-5 text-center cursor-pointer transition-all bg-blue-500/[0.03] hover:bg-blue-500/[0.08] mb-4"
                    ),
                    select_field("Target Cloud Folder", "folder", [(f, f) for f in FOLDERS]),
                    input_field("Custom Display Name (Optional)", "custom_name", placeholder="Leave blank to keep original filename", required=False),
                    id="cloud-upload-form-fields"
                ),
                # Real-time Streaming Upload Progress Bar
                Div(
                    Div(
                        Span("Uploading to Server...", id="cloud-upload-status", cls="text-xs font-mono font-medium text-cyan-300"),
                        Span("0%", id="cloud-upload-percent", cls="text-xs font-mono font-bold text-white"),
                        cls="flex items-center justify-between mb-1.5"
                    ),
                    Div(
                        Div(id="cloud-upload-progress-bar", cls="h-full bg-gradient-to-r from-blue-600 via-cyan-500 to-indigo-500 rounded-full transition-all duration-150", style="width: 0%"),
                        cls="w-full h-2 rounded-full bg-slate-800 border border-white/10 overflow-hidden mb-2"
                    ),
                    Div(
                        Span("0 / 0 MB", id="cloud-upload-bytes", cls="text-[11px] font-mono text-slate-400"),
                        Span("0 MB/s", id="cloud-upload-speed", cls="text-[11px] font-mono text-slate-400"),
                        cls="flex items-center justify-between"
                    ),
                    id="cloud-upload-progress-container",
                    cls="hidden mb-4 p-3.5 rounded-xl bg-blue-950/40 border border-blue-500/25"
                ),
                Div(
                    btn_ghost("Cancel", type="button", onclick="cancelCloudUpload()"),
                    btn_primary(icon("cloud_upload", "text-sm mr-1.5"), "Upload to Supabase Cloud", id="cloud-upload-submit-btn", type="submit"),
                    cls="flex justify-end gap-3 mt-4 pt-3 border-t border-white/[0.08]"
                ),
                onsubmit="return handleFastCloudUpload(event);",
                method="post",
                action="/files/upload",
                enctype="multipart/form-data"
            ),
            cls="relative z-10 w-full max-w-lg mx-auto mt-16 border border-blue-500/30 bg-[#0f172a] shadow-2xl"
        ),
        upload_script,
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

    download_script = Script("""
    function handleFileDownload(btn) {
        var icon = btn.querySelector('.dl-icon');
        var text = btn.querySelector('.dl-text');
        var spinner = btn.querySelector('.dl-spinner');
        if (text) text.textContent = 'Preparing...';
        if (icon) icon.classList.add('hidden');
        if (spinner) spinner.classList.remove('hidden');
        btn.classList.add('pointer-events-none', 'opacity-85');

        setTimeout(function() {
            if (text) text.textContent = 'Downloading...';
        }, 400);

        setTimeout(function() {
            if (text) text.textContent = 'Download';
            if (icon) icon.classList.remove('hidden');
            if (spinner) spinner.classList.add('hidden');
            btn.classList.remove('pointer-events-none', 'opacity-85');
        }, 2800);
    }
    """)

    file_list = card(
        Div(
            H3(f"Stored Documents & Assets ({len(active_files)})", cls="font-heading font-semibold text-lg text-white"),
            Span(f"Viewing: {folder.upper()}", cls="text-xs font-mono text-slate-400 bg-white/5 border border-white/10 px-2.5 py-1 rounded-lg"),
            cls="flex items-center justify-between mb-4 pb-2 border-b border-white/5"
        ),
        Div(
            *[file_row(f, idx) for idx, f in enumerate(active_files)] or [
                Div(
                    icon("cloud_off", "text-4xl text-slate-500 mb-2"),
                    P("No files stored in this folder yet. Click 'Upload File to Cloud' above to add documents.", cls="text-slate-400 text-sm text-center font-mono"),
                    cls="text-center py-12"
                )
            ],
            cls="space-y-3"
        ),
        cls="shadow-2xl border border-white/[0.06]"
    )

    return page(session, u, "Files", header, alerts, stats, folder_chips, file_list, upload_modal, link_modal, download_script)

@rt("/files/upload", methods=["POST"])
async def files_upload_post(req: Request, session, folder: str, upload_file: UploadFile, custom_name: str = ""):
    u = current_user(session)
    is_json = "application/json" in req.headers.get("accept", "")

    if not u or session.get("view_as"):
        if is_json:
            return JSONResponse({"error": "Session expired or invalid. Please sign in again."}, status_code=401)
        return go("/login")

    if not upload_file or not upload_file.filename:
        if is_json:
            return JSONResponse({"error": "No file was selected for upload."}, status_code=400)
        return go("/files?error=No+file+was+selected+for+upload.")

    try:
        contents = await upload_file.read()
    except Exception as e:
        if is_json:
            return JSONResponse({"error": f"Could not read uploaded file: {str(e)[:50]}"}, status_code=400)
        return go(f"/files?error=Could+not+read+file:+{str(e)[:50]}")

    if not contents:
        if is_json:
            return JSONResponse({"error": "Uploaded file is empty (0 bytes)."}, status_code=400)
        return go("/files?error=Uploaded+file+is+empty.")

    original_name = Path(upload_file.filename).name
    display_name = custom_name.strip() if custom_name and custom_name.strip() else original_name
    ext = Path(original_name).suffix
    storage_path = f"{folder.lower().replace(' ', '_')}/{uuid.uuid4().hex[:8]}_{original_name}"
    content_type = upload_file.content_type or "application/octet-stream"

    # Ensure bucket is public
    ensure_bucket_public()

    # Non-blocking async upload to Supabase Storage bucket 'club-files'
    try:
        await asyncio.to_thread(
            supabase.storage.from_("club-files").upload,
            storage_path,
            contents,
            {"content-type": content_type, "upsert": "true"}
        )
        encoded_storage_path = urllib.parse.quote(storage_path, safe="/")
        pub_url = f"{_url}/storage/v1/object/public/club-files/{encoded_storage_path}"
    except Exception as e:
        print("Supabase cloud upload failed:", e)
        if is_json:
            return JSONResponse({"error": f"Supabase storage error: {str(e)[:80]}"}, status_code=500)
        return go(f"/files?error=Supabase+storage+error:+{str(e)[:80]}")

    # Record in files table asynchronously
    try:
        res = await asyncio.to_thread(
            lambda: supabase.table("files").insert({
                "name": display_name,
                "folder": folder,
                "path": storage_path,
                "link_url": pub_url,
                "size": len(contents),
                "mime": content_type,
                "uploader": u["id"]
            }).execute()
        )

        if res.data:
            invalidate_cache("files_")
            log_activity(session, "cloud_file_upload", "files", res.data[0]["id"], f"Uploaded '{display_name}' ({format_bytes(len(contents))}) to Supabase Cloud")
    except Exception as e:
        print("Files table record insertion failed:", e)

    if is_json:
        return JSONResponse({
            "status": "success",
            "message": f"File '{display_name}' successfully stored in Supabase Cloud Storage!",
            "name": display_name,
            "url": pub_url,
            "size": len(contents),
            "folder": folder,
            "redirect": f"/files?msg=File+'{display_name}'+successfully+stored+in+Supabase+Cloud+Storage!"
        })

    return go(f"/files?msg=File+'{display_name}'+successfully+stored+in+Supabase+Cloud+Storage!")

@rt("/files/{fid}/download", methods=["GET"])
def files_download_get(session, fid: int):
    u = current_user(session)
    if not u:
        return go("/login")

    try:
        f = supabase.table("files").select("*").eq("id", fid).single().execute().data
    except Exception as e:
        print("Download lookup error:", e)
        return go("/files?error=File+lookup+failed.")

    if not f:
        return go("/files?error=File+not+found.")

    path = f.get("path") or ""
    link_url = f.get("link_url") or ""

    # External cloud URLs (Drive, GitHub, Dropbox, etc.)
    if link_url.startswith("http") and "supabase.co" not in link_url:
        return RedirectResponse(link_url, status_code=302)

    # Guarantee bucket is public
    ensure_bucket_public()

    if path and not path.startswith("http"):
        encoded_path = urllib.parse.quote(path, safe="/")
        download_url = f"{_url}/storage/v1/object/public/club-files/{encoded_path}"
    elif link_url:
        download_url = link_url
    else:
        return go("/files?error=File+path+is+missing.")

    return RedirectResponse(download_url, status_code=302)

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
