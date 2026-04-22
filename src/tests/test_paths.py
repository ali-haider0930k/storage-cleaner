"""Assert that the path-safety layer rejects dangerous paths."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paths import is_path_forbidden, is_within, is_drive_root, norm


def expect(cond, msg):
    if not cond:
        print(f"FAIL: {msg}")
        return 1
    print(f"PASS: {msg}")
    return 0


def main():
    failures = 0

    # --- is_within: basic containment ---
    failures += expect(is_within(r"C:\Windows\System32", r"C:\Windows"), "child is within parent")
    failures += expect(not is_within(r"C:\Windows", r"C:\Windows\System32"), "parent is NOT within child")
    failures += expect(is_within(r"C:\Windows", r"C:\Windows"), "same path is within (non-strict)")
    failures += expect(not is_within(r"C:\Windows", r"C:\Windows", strict=True), "same path NOT within in strict mode")

    # Prefix false positive must not happen (c:\programs vs c:\program files)
    failures += expect(not is_within(r"C:\Program Files", r"C:\Program"), "sibling prefix must not match")

    # --- is_drive_root ---
    failures += expect(is_drive_root("C:\\"), "C:\\ is drive root")
    failures += expect(is_drive_root("D:\\"), "D:\\ is drive root")
    failures += expect(not is_drive_root(r"C:\Windows"), "C:\\Windows is NOT drive root")

    # --- is_path_forbidden: system paths ---
    forbid_system = [
        r"C:\Windows",
        r"C:\Windows\System32",
        r"C:\Windows\System32\cmd.exe",
        r"C:\Windows\SysWOW64",
        r"C:\Windows\WinSxS",
        r"C:\Program Files",
        r"C:\Program Files\Any\thing",
        r"C:\Program Files (x86)\Foo",
        "C:\\",
        "D:\\",
    ]
    for p in forbid_system:
        ok, reason = is_path_forbidden(p)
        failures += expect(ok, f"must reject system path: {p} (reason={reason!r})")

    # --- is_path_forbidden: user data ---
    user_profile = os.environ.get("USERPROFILE", "")
    if user_profile:
        forbid_user = [
            os.path.join(user_profile, "Documents"),
            os.path.join(user_profile, "Documents", "file.txt"),
            os.path.join(user_profile, "Pictures"),
            os.path.join(user_profile, "Videos", "movie.mp4"),
        ]
        for p in forbid_user:
            ok, reason = is_path_forbidden(p)
            failures += expect(ok, f"must reject user-data path: {p} (reason={reason!r})")

    # --- is_path_forbidden: allowed paths ---
    temp = os.environ.get("TEMP", "")
    if temp:
        p = os.path.join(temp, "some_cache_file.tmp")
        ok, reason = is_path_forbidden(p)
        failures += expect(not ok, f"must allow user-temp path: {p}")

    localapp = os.environ.get("LOCALAPPDATA", "")
    if localapp:
        p = os.path.join(localapp, "Google", "Chrome", "User Data", "Default", "Cache", "f_000001")
        ok, reason = is_path_forbidden(p)
        failures += expect(not ok, f"must allow chrome cache path: {p}")

    # Very short path rejected
    ok, _ = is_path_forbidden("C:")
    failures += expect(ok, "must reject too-short path")

    # Empty path rejected
    ok, _ = is_path_forbidden("")
    failures += expect(ok, "must reject empty path")

    # --- norm idempotency ---
    failures += expect(norm(r"C:\Windows") == norm(r"c:\WINDOWS\\"), "norm is case- and trailing-slash-insensitive")

    print()
    if failures:
        print(f"\n{failures} test(s) FAILED")
        sys.exit(1)
    print("ALL PATHS TESTS PASSED")


if __name__ == "__main__":
    main()
