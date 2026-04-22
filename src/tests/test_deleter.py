"""Verify deleter enforces containment: forbidden paths are rejected, allowed ones are deleted via send2trash."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deleter import delete_paths


def expect(cond, msg):
    if not cond:
        print(f"FAIL: {msg}")
        return 1
    print(f"PASS: {msg}")
    return 0


def main():
    failures = 0

    with tempfile.TemporaryDirectory(prefix="sc_test_allowed_") as allowed_root:
        # Create some files in the allowed dir
        f1 = os.path.join(allowed_root, "test1.tmp")
        f2 = os.path.join(allowed_root, "test2.tmp")
        with open(f1, "w") as fh:
            fh.write("A" * 100)
        with open(f2, "w") as fh:
            fh.write("B" * 200)

        # Attempt a forbidden delete: C:\Windows\System32\cmd.exe
        # (Should be rejected even though the user listed it)
        r = delete_paths(
            [r"C:\Windows\System32\cmd.exe", r"C:\Program Files"],
            allowed_roots=[allowed_root],
            permanent=False,
        )
        failures += expect(r["deleted"] == 0, "forbidden paths not deleted")
        failures += expect(len(r["failed"]) == 2, "both forbidden paths recorded as failed")
        failures += expect(all("blocked" in f["reason"] for f in r["failed"]), "failure reasons mention 'blocked'")

        # Attempt a delete OUTSIDE allowed roots (but not in blocklist)
        with tempfile.NamedTemporaryFile(delete=False, prefix="sc_outside_", suffix=".txt") as fh:
            outside_path = fh.name
            fh.write(b"X")
        try:
            r = delete_paths([outside_path], allowed_roots=[allowed_root], permanent=False)
            failures += expect(r["deleted"] == 0, "path outside allowed roots not deleted")
            failures += expect(
                len(r["failed"]) == 1 and "outside allowed roots" in r["failed"][0]["reason"],
                "out-of-roots rejection reason correct",
            )
        finally:
            if os.path.exists(outside_path):
                os.remove(outside_path)

        # Allowed delete (uses send2trash)
        failures += expect(os.path.exists(f1), "setup: f1 exists before delete")
        r = delete_paths([f1, f2], allowed_roots=[allowed_root], permanent=False)
        failures += expect(r["deleted"] == 2, "two allowed files deleted")
        failures += expect(r["bytes_freed"] >= 300, f"bytes_freed reported correctly (got {r['bytes_freed']})")
        failures += expect(not os.path.exists(f1) and not os.path.exists(f2), "files no longer present after send2trash")

    # Empty paths
    r = delete_paths([], allowed_roots=[], permanent=False)
    failures += expect(r["deleted"] == 0 and r["total_attempted"] == 0, "empty path list returns empty result")

    if failures:
        print(f"\n{failures} test(s) FAILED")
        sys.exit(1)
    print("\nALL DELETER TESTS PASSED")


if __name__ == "__main__":
    main()
