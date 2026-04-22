"""Safe delete with containment enforcement. Default: send to Recycle Bin."""
import os
import shutil

from send2trash import send2trash

from paths import is_path_forbidden, is_within, norm


def delete_paths(paths, allowed_roots, permanent=False, progress_cb=None, protect_user_data=True):
    deleted = 0
    failed = []
    bytes_freed = 0
    total = len(paths)
    allowed_norm = [norm(r) for r in allowed_roots if r]

    for i, p in enumerate(paths):
        try:
            forbidden, reason = is_path_forbidden(p, protect_user_data=protect_user_data)
            if forbidden:
                failed.append({"path": p, "reason": f"blocked ({reason})"})
                continue
            if allowed_norm and not any(is_within(p, r) for r in allowed_norm):
                failed.append({"path": p, "reason": "outside allowed roots"})
                continue
            if not os.path.exists(p):
                failed.append({"path": p, "reason": "not found"})
                continue
            if os.path.islink(p):
                failed.append({"path": p, "reason": "symlink"})
                continue

            try:
                if os.path.isdir(p):
                    size = _dir_size(p)
                else:
                    size = os.path.getsize(p)
            except OSError:
                size = 0

            if permanent:
                if os.path.isdir(p):
                    shutil.rmtree(p, ignore_errors=False)
                else:
                    os.remove(p)
            else:
                send2trash(p)

            deleted += 1
            bytes_freed += size
        except Exception as e:
            failed.append({"path": p, "reason": type(e).__name__ + ": " + str(e)})

        if progress_cb and (i + 1) % 20 == 0:
            try:
                progress_cb(i + 1, total, bytes_freed)
            except Exception:
                pass

    if progress_cb:
        try:
            progress_cb(total, total, bytes_freed)
        except Exception:
            pass

    return {
        "deleted": deleted,
        "failed": failed,
        "bytes_freed": bytes_freed,
        "total_attempted": total,
    }


def _dir_size(path):
    total = 0
    try:
        for root, dirs, files in os.walk(path, onerror=lambda e: None, followlinks=False):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except OSError:
                    continue
    except OSError:
        return 0
    return total
