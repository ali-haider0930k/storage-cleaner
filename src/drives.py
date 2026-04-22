"""Enumerate fixed drives with free-space info."""
import ctypes
import os

import psutil


def _get_volume_label(mountpoint):
    if os.name != "nt":
        return ""
    root = mountpoint if mountpoint.endswith("\\") else mountpoint + "\\"
    vol = ctypes.create_unicode_buffer(261)
    fs = ctypes.create_unicode_buffer(261)
    try:
        ok = ctypes.windll.kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(root),
            vol, 260,
            None, None, None,
            fs, 260,
        )
        return vol.value if ok else ""
    except OSError:
        return ""


def list_drives():
    out = []
    try:
        partitions = psutil.disk_partitions(all=False)
    except Exception:
        partitions = []
    for part in partitions:
        if os.name == "nt" and "fixed" not in part.opts:
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except (PermissionError, OSError):
            continue
        label = _get_volume_label(part.mountpoint)
        out.append({
            "mountpoint": part.mountpoint,
            "label": label or "Local Disk",
            "fstype": part.fstype,
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent": usage.percent,
        })
    return out
