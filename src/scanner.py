"""Background scanning: category scans and large-file scans."""
import fnmatch
import glob
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class ScanItem:
    path: str
    size: int
    mtime: float


@dataclass
class ScanState:
    scan_id: str
    category_id: str
    tier: str
    status: str = "pending"
    items: list = field(default_factory=list)
    total_bytes: int = 0
    total_files: int = 0
    errors: list = field(default_factory=list)
    roots: list = field(default_factory=list)
    cancel_event: threading.Event = field(default_factory=threading.Event)
    error_msg: str = ""
    started_at: float = 0.0
    finished_at: float = 0.0


SCANS: dict = {}
SCANS_LOCK = threading.Lock()

_PROGRESS_EVERY_N = 500


def new_scan(category_id, tier):
    s = ScanState(scan_id=str(uuid.uuid4()), category_id=category_id, tier=tier)
    s.started_at = time.time()
    with SCANS_LOCK:
        SCANS[s.scan_id] = s
    return s


def get_scan(scan_id):
    with SCANS_LOCK:
        return SCANS.get(scan_id)


def cancel_scan(scan_id):
    s = get_scan(scan_id)
    if not s:
        return False
    s.cancel_event.set()
    return True


def _expand_root(path_pattern):
    expanded = os.path.expandvars(path_pattern)
    if any(c in expanded for c in "*?["):
        try:
            return glob.glob(expanded)
        except OSError:
            return []
    return [expanded]


def _recycle_bin_roots():
    from drives import list_drives
    roots = []
    for d in list_drives():
        rb = os.path.join(d["mountpoint"], "$Recycle.Bin")
        if not os.path.exists(rb):
            continue
        try:
            with os.scandir(rb) as it:
                for sub in it:
                    try:
                        if sub.is_dir(follow_symlinks=False):
                            roots.append(sub.path)
                    except (PermissionError, OSError):
                        continue
        except (PermissionError, OSError):
            continue
    return roots


def expand_roots_for_entry(entry):
    if entry.get("special") == "recycle_bin":
        return _recycle_bin_roots()
    roots = []
    for p in entry.get("paths", []):
        roots.extend(_expand_root(p))
    return [r for r in roots if os.path.exists(r)]


def _iter_files(root, recursive, pattern, max_age_days, cancel_event, skip_prefixes=None):
    """Yield (path, size, mtime). Silently skip permission errors and symlinks."""
    age_cutoff = None
    if max_age_days is not None:
        age_cutoff = time.time() - (max_age_days * 86400)
    pattern_lower = pattern.lower() if pattern else None
    match_all = (not pattern) or pattern == "*"
    skip_norm = [os.path.normcase(s) for s in skip_prefixes] if skip_prefixes else None

    def _should_skip_dir(path):
        if not skip_norm:
            return False
        pn = os.path.normcase(path)
        return any(pn == sp or pn.startswith(sp + os.sep) for sp in skip_norm)

    if not recursive:
        try:
            with os.scandir(root) as it:
                for entry in it:
                    if cancel_event.is_set():
                        return
                    try:
                        if entry.is_symlink():
                            continue
                        if not entry.is_file(follow_symlinks=False):
                            continue
                        if not match_all and not fnmatch.fnmatch(entry.name.lower(), pattern_lower):
                            continue
                        st = entry.stat(follow_symlinks=False)
                        if age_cutoff is not None and st.st_mtime > age_cutoff:
                            continue
                        yield (entry.path, st.st_size, st.st_mtime)
                    except (PermissionError, OSError):
                        continue
        except (PermissionError, OSError, FileNotFoundError):
            return
        return

    stack = [root]
    while stack:
        if cancel_event.is_set():
            return
        current = stack.pop()
        if _should_skip_dir(current):
            continue
        try:
            with os.scandir(current) as it:
                for entry in it:
                    if cancel_event.is_set():
                        return
                    try:
                        if entry.is_symlink():
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            if not _should_skip_dir(entry.path):
                                stack.append(entry.path)
                            continue
                        if not entry.is_file(follow_symlinks=False):
                            continue
                        if not match_all and not fnmatch.fnmatch(entry.name.lower(), pattern_lower):
                            continue
                        st = entry.stat(follow_symlinks=False)
                        if age_cutoff is not None and st.st_mtime > age_cutoff:
                            continue
                        yield (entry.path, st.st_size, st.st_mtime)
                    except (PermissionError, OSError):
                        continue
        except (PermissionError, OSError, FileNotFoundError):
            continue


def _run_category_scan(state: ScanState, entry: dict, progress_cb):
    recursive = entry.get("recursive", True)
    pattern = entry.get("pattern", "*")
    max_age = entry.get("max_age_days")
    count = 0
    for root in state.roots:
        if state.cancel_event.is_set():
            break
        for path, size, mtime in _iter_files(root, recursive, pattern, max_age, state.cancel_event):
            state.items.append(ScanItem(path=path, size=size, mtime=mtime))
            state.total_bytes += size
            state.total_files += 1
            count += 1
            if progress_cb and count % _PROGRESS_EVERY_N == 0:
                try:
                    progress_cb(state, path)
                except Exception:
                    pass


def scan_category_async(entry, progress_cb, complete_cb):
    state = new_scan(entry["id"], entry["tier"])
    state.roots = expand_roots_for_entry(entry)

    def worker():
        state.status = "running"
        try:
            _run_category_scan(state, entry, progress_cb)
            state.status = "cancelled" if state.cancel_event.is_set() else "done"
        except Exception as e:
            state.status = "error"
            state.error_msg = str(e)
        finally:
            state.finished_at = time.time()
            if complete_cb:
                try:
                    complete_cb(state)
                except Exception:
                    pass

    threading.Thread(target=worker, daemon=True).start()
    return state


def scan_all_async(categories, progress_cb, complete_cb, per_category_cb):
    state = new_scan("all", "MIXED")

    def worker():
        state.status = "running"
        try:
            for cat in categories:
                if state.cancel_event.is_set():
                    break
                sub = new_scan(cat["id"], cat["tier"])
                sub.roots = expand_roots_for_entry(cat)
                sub.status = "running"
                try:
                    _run_category_scan(sub, cat, None)
                    sub.status = "cancelled" if state.cancel_event.is_set() else "done"
                except Exception as e:
                    sub.status = "error"
                    sub.error_msg = str(e)
                finally:
                    sub.finished_at = time.time()
                state.total_bytes += sub.total_bytes
                state.total_files += sub.total_files
                if per_category_cb:
                    try:
                        per_category_cb(sub)
                    except Exception:
                        pass
                if progress_cb:
                    try:
                        progress_cb(state, cat["id"])
                    except Exception:
                        pass
            state.status = "cancelled" if state.cancel_event.is_set() else "done"
        except Exception as e:
            state.status = "error"
            state.error_msg = str(e)
        finally:
            state.finished_at = time.time()
            if complete_cb:
                try:
                    complete_cb(state)
                except Exception:
                    pass

    threading.Thread(target=worker, daemon=True).start()
    return state


def scan_large_files_async(roots, min_size, top_n, progress_cb, complete_cb, skip_prefixes=None):
    state = new_scan("large_files", "USER")
    state.roots = [os.path.expandvars(r) for r in roots if r]

    def worker():
        state.status = "running"
        try:
            found = []
            count = 0
            for root in state.roots:
                if state.cancel_event.is_set():
                    break
                if not os.path.exists(root):
                    continue
                for path, size, mtime in _iter_files(root, True, "*", None, state.cancel_event, skip_prefixes):
                    count += 1
                    if progress_cb and count % _PROGRESS_EVERY_N == 0:
                        try:
                            progress_cb(state, path)
                        except Exception:
                            pass
                    if size >= min_size:
                        found.append(ScanItem(path=path, size=size, mtime=mtime))
            found.sort(key=lambda x: x.size, reverse=True)
            state.items = found[:top_n]
            state.total_files = len(state.items)
            state.total_bytes = sum(i.size for i in state.items)
            state.status = "cancelled" if state.cancel_event.is_set() else "done"
        except Exception as e:
            state.status = "error"
            state.error_msg = str(e)
        finally:
            state.finished_at = time.time()
            if complete_cb:
                try:
                    complete_cb(state)
                except Exception:
                    pass

    threading.Thread(target=worker, daemon=True).start()
    return state


def pc_wide_skip_prefixes():
    """Subtrees to skip when scanning an entire drive for big files."""
    from drives import list_drives
    prefixes = [
        os.path.expandvars(r"%ProgramFiles%\WindowsApps"),
        os.path.expandvars(r"%ProgramData%\Packages"),
        os.path.expandvars(r"%ProgramData%\Microsoft\Windows\WER"),
    ]
    for d in list_drives():
        mp = d["mountpoint"].rstrip("\\").rstrip("/")
        for sub in ("Windows", "Windows.old", "$Recycle.Bin", "System Volume Information", "Config.Msi", "$WinREAgent", "$GetCurrent", "OneDriveTemp"):
            prefixes.append(mp + os.sep + sub)
    return prefixes
