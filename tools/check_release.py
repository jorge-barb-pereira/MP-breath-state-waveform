"""Verify explicit working-tree and tracked-file boundaries; never upload."""

from pathlib import Path
import subprocess
import sys


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    entries = (root / "PUBLICATION_ALLOWLIST.txt").read_text(encoding="utf-8").splitlines()
    allowed = set(entries)
    if len(allowed) != len(entries) or any(
        not item or "\\" in item or item.startswith("/") or ".." in Path(item).parts
        for item in entries
    ):
        print("FAIL: malformed or duplicate allowlist entry.")
        return 1
    command = ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(root)]
    try:
        tracked = subprocess.run(command + ["ls-files", "-z"], check=True, capture_output=True).stdout
        others = subprocess.run(command + ["ls-files", "--others", "--exclude-standard", "-z"],
                                check=True, capture_output=True).stdout
    except (OSError, subprocess.CalledProcessError):
        print("FAIL: local Git inventory unavailable.")
        return 1
    tracked_names = {item.decode("utf-8") for item in tracked.split(b"\0") if item}
    other_names = {item.decode("utf-8") for item in others.split(b"\0") if item}
    if tracked_names != allowed or other_names - allowed:
        print("FAIL: tracked or non-ignored files differ from the publication allowlist.")
        return 1
    for entry in entries:
        path = root / entry
        if not path.is_file() or path.is_symlink() or any(
            (root / parent).is_symlink() for parent in path.relative_to(root).parents
            if parent != Path(".")
        ):
            print("FAIL: allowlisted entry is missing or is a symbolic link.")
            return 1
        try:
            path.read_text(encoding="utf-8")
        except (UnicodeError, OSError):
            print("FAIL: a release file is not readable UTF-8 text.")
            return 1
    print(f"PASS: {len(allowed)} allowlisted UTF-8 files; no additional non-ignored files.")
    print("Manual content, staged-blob, history, and permission review is still required.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
