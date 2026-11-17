"""Download a public file from Google Drive (with the confirmation step for a large file).

Usage:

    python3 -I tools/fetch_drive.py FILE_ID OUTPUT_PATH
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


def main() -> int:
    file_id, output = sys.argv[1], Path(sys.argv[2])
    output.parent.mkdir(parents=True, exist_ok=True)
    first = f"https://drive.google.com/uc?id={file_id}&export=download"
    page = output.with_suffix(output.suffix + ".page")
    subprocess.run(["curl", "-sL", "--max-time", "120", "-A", "generic-client", "-o", str(page),
                    first], check=True)  # fmt: skip
    head = page.read_bytes()[:4096]
    if b"<html" not in head.lower() and b"<!doctype" not in head.lower():
        page.replace(output)  # a small file comes at once
        print(f"{output}: {output.stat().st_size} bytes")
        return 0
    text = page.read_text(encoding="utf-8", errors="replace")
    action = re.search(r'action="([^"]+)"', text)
    fields = dict(re.findall(r'name="([^"]+)" value="([^"]*)"', text))
    if not action or "id" not in fields:
        print("the page has no download form", file=sys.stderr)
        return 1
    query = "&".join(f"{name}={value}" for name, value in fields.items())
    subprocess.run(["curl", "-L", "--fail", "--silent", "--show-error", "-A", "generic-client",
                    "-o", str(output), f"{action.group(1)}?{query}"], check=True)  # fmt: skip
    page.unlink()
    print(f"{output}: {output.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
