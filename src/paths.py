"""Path normalization and safety checks."""
import os


SYSTEM_BLOCKLIST = [
    r"%SystemRoot%\System32",
    r"%SystemRoot%\SysWOW64",
    r"%SystemRoot%\WinSxS",
    r"%SystemRoot%\servicing",
    r"%SystemRoot%\Boot",
    r"%SystemRoot%\Fonts",
    r"%SystemRoot%\assembly",
    r"%ProgramFiles%",
    r"%ProgramFiles(x86)%",
    r"%ProgramData%\Microsoft\Crypto",
    r"%ProgramData%\Microsoft\Windows\Start Menu",
    r"C:\Recovery",
    r"C:\System Volume Information",
    r"C:\Boot",
]

PROHIBITED_EXACT = [
    r"%SystemRoot%",
    r"%SystemDrive%",
    r"%USERPROFILE%",
    r"%ProgramData%",
    r"%LOCALAPPDATA%",
    r"%APPDATA%",
]

USER_DATA_BLOCKLIST = [
    r"%USERPROFILE%\Documents",
    r"%USERPROFILE%\Pictures",
    r"%USERPROFILE%\Music",
    r"%USERPROFILE%\Videos",
    r"%USERPROFILE%\OneDrive",
    r"%APPDATA%",
]


def norm(path):
    if not path:
        return ""
    expanded = os.path.expandvars(path)
    try:
        resolved = os.path.realpath(os.path.abspath(expanded))
    except (OSError, ValueError):
        resolved = os.path.abspath(expanded)
    return os.path.normcase(resolved)


def is_within(child, parent, strict=False):
    c = norm(child)
    p = norm(parent)
    if not c or not p:
        return False
    if c == p:
        return not strict
    sep = os.sep
    p_prefix = p if p.endswith(sep) else p + sep
    return c.startswith(p_prefix)


def is_drive_root(path):
    n = norm(path)
    return len(n) == 3 and n[1:] == ":" + os.sep


def _expand_all(paths):
    return [norm(p) for p in paths if p]


def is_path_forbidden(path, protect_user_data=True):
    if not path:
        return True, "empty"
    n = norm(path)
    if len(n) < 4:
        return True, "too short"
    if is_drive_root(path):
        return True, "drive root"
    for exact in _expand_all(PROHIBITED_EXACT):
        if exact and n == exact:
            return True, f"top-level:{exact}"
    for blocked in _expand_all(SYSTEM_BLOCKLIST):
        if is_within(n, blocked):
            return True, f"system:{blocked}"
    if protect_user_data:
        for blocked in _expand_all(USER_DATA_BLOCKLIST):
            if is_within(n, blocked):
                return True, f"user-data:{blocked}"
    return False, ""


def human_bytes(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} {unit}"
        n /= 1024
    return f"{n:.1f} PB"
