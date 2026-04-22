"""JS-facing API. Every public method returns JSON-serializable data."""
import os
import platform
import sys
import threading

import webview

from deleter import delete_paths
from drives import list_drives as _list_drives
from progress import get_dispatcher
from registry import SCAN_CATEGORIES, by_id
from scanner import (
    SCANS,
    SCANS_LOCK,
    cancel_scan as _cancel_scan,
    expand_roots_for_entry,
    get_scan,
    pc_wide_skip_prefixes,
    scan_all_async,
    scan_category_async,
    scan_large_files_async,
)


class Api:
    def __init__(self):
        self.window = None
        self.dispatcher = get_dispatcher()

    # ----- drives & categories -----

    def list_drives(self):
        try:
            return _list_drives()
        except Exception as e:
            return {"error": str(e)}

    def list_categories(self):
        return [
            {
                "id": c["id"],
                "label": c["label"],
                "tier": c["tier"],
                "desc": c["desc"],
                "icon": c.get("icon", "file"),
                "force_permanent": c.get("force_permanent", False),
            }
            for c in SCAN_CATEGORIES
        ]

    # ----- scans -----

    def scan_category(self, category_id):
        cat = by_id(category_id)
        if not cat:
            return {"error": "unknown category"}
        state = scan_category_async(
            cat,
            progress_cb=self._scan_progress,
            complete_cb=self._scan_complete,
        )
        return {"scan_id": state.scan_id}

    def scan_all_categories(self):
        state = scan_all_async(
            SCAN_CATEGORIES,
            progress_cb=self._scan_all_progress,
            complete_cb=self._scan_all_complete,
            per_category_cb=self._scan_complete,
        )
        return {"scan_id": state.scan_id}

    def scan_large_files(self, roots=None, min_size_mb=100, top_n=200, skip_system=False):
        roots = list(roots) if roots else _default_large_roots()
        try:
            min_bytes = int(min_size_mb) * 1024 * 1024
        except (TypeError, ValueError):
            min_bytes = 100 * 1024 * 1024
        try:
            top_n_i = int(top_n)
        except (TypeError, ValueError):
            top_n_i = 200
        skip_prefixes = pc_wide_skip_prefixes() if skip_system else None
        state = scan_large_files_async(
            roots, min_bytes, top_n_i,
            progress_cb=lambda s, path: self.dispatcher.emit("scan_progress", {
                "scan_id": s.scan_id,
                "category_id": "large_files",
                "files_scanned": s.total_files,
                "bytes_seen": 0,
                "current": path,
            }),
            complete_cb=self._scan_complete,
            skip_prefixes=skip_prefixes,
        )
        return {"scan_id": state.scan_id}

    def scan_biggest_on_pc(self, top_n=20):
        drives = _list_drives()
        roots = [d["mountpoint"] for d in drives]
        return self.scan_large_files(roots=roots, min_size_mb=1, top_n=int(top_n or 20), skip_system=True)

    def cancel_scan(self, scan_id):
        return _cancel_scan(scan_id)

    def get_scan_result(self, scan_id):
        s = get_scan(scan_id)
        if not s:
            return {"error": "unknown scan"}
        return _result_for_js(s)

    # ----- delete -----

    def delete_files(self, category_id, paths, permanent=False):
        paths = list(paths or [])
        if not paths:
            return {"deleted": 0, "failed": [], "bytes_freed": 0, "total_attempted": 0}

        allowed_roots = self._allowed_roots_for(category_id)
        if allowed_roots is None:
            return {"error": f"unknown category: {category_id}"}

        use_permanent = bool(permanent)
        if category_id == "recycle_bin":
            use_permanent = True

        protect_user = category_id != "large_files"

        def worker():
            result = delete_paths(
                paths, allowed_roots, permanent=use_permanent,
                progress_cb=lambda done, total, freed: self.dispatcher.emit("delete_progress", {
                    "done": done, "total": total, "bytes_freed": freed,
                }),
                protect_user_data=protect_user,
            )
            self.dispatcher.emit("delete_complete", result)

        threading.Thread(target=worker, daemon=True).start()
        return {"started": True, "count": len(paths), "permanent": use_permanent}

    def _allowed_roots_for(self, category_id):
        if category_id == "large_files":
            with SCANS_LOCK:
                lf = [s for s in SCANS.values() if s.category_id == "large_files"]
            if not lf:
                return None
            latest = max(lf, key=lambda s: s.started_at)
            return list(latest.roots)
        cat = by_id(category_id)
        if not cat:
            return None
        return expand_roots_for_entry(cat)

    # ----- misc -----

    def open_folder(self, path):
        try:
            target = path
            if not target:
                return False
            if not os.path.exists(target):
                target = os.path.dirname(target)
            if not target or not os.path.exists(target):
                return False
            os.startfile(target)
            return True
        except Exception:
            return False

    def choose_folder(self):
        try:
            if self.window is None:
                return None
            result = self.window.create_file_dialog(webview.FOLDER_DIALOG)
            if not result:
                return None
            if isinstance(result, (list, tuple)):
                return result[0]
            return result
        except Exception:
            return None

    def default_large_roots(self):
        return _default_large_roots()

    def get_version(self):
        return {
            "app": "1.0.0",
            "python": sys.version.split(" ", 1)[0],
            "platform": platform.platform(),
        }

    # ----- callbacks -----

    def _scan_progress(self, state, current_path):
        self.dispatcher.emit("scan_progress", {
            "scan_id": state.scan_id,
            "category_id": state.category_id,
            "files_scanned": state.total_files,
            "bytes_seen": state.total_bytes,
            "current": current_path,
        })

    def _scan_complete(self, state):
        self.dispatcher.emit("scan_complete", {
            "scan_id": state.scan_id,
            "category_id": state.category_id,
            "result": _result_for_js(state),
        })

    def _scan_all_progress(self, state, category_done):
        self.dispatcher.emit("scan_all_progress", {
            "scan_id": state.scan_id,
            "category_done": category_done,
            "total_bytes": state.total_bytes,
            "total_files": state.total_files,
        })

    def _scan_all_complete(self, state):
        self.dispatcher.emit("scan_all_complete", {
            "scan_id": state.scan_id,
            "total_bytes": state.total_bytes,
            "total_files": state.total_files,
            "status": state.status,
        })


def _default_large_roots():
    roots = []
    up = os.environ.get("USERPROFILE", "")
    if up:
        for sub in ("Downloads", "Desktop", "Documents", "Videos", "Pictures"):
            p = os.path.join(up, sub)
            if os.path.exists(p):
                roots.append(p)
    return roots


_MAX_ITEMS_JS = 5000


def _result_for_js(state):
    items_sorted = sorted(state.items, key=lambda x: x.size, reverse=True)
    items = [
        {"path": i.path, "size": i.size, "mtime": i.mtime}
        for i in items_sorted[:_MAX_ITEMS_JS]
    ]
    return {
        "scan_id": state.scan_id,
        "category_id": state.category_id,
        "tier": state.tier,
        "status": state.status,
        "items": items,
        "total_bytes": state.total_bytes,
        "total_files": state.total_files,
        "errors": state.errors,
        "truncated": len(state.items) > _MAX_ITEMS_JS,
    }
