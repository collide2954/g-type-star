"""List or unpack an archive (RAR, ZIP, 7z, tar) with the libarchive library of the system.

Usage:

    uv run --with libarchive-c python -I tools/unpack.py list ARCHIVE
    uv run --with libarchive-c python -I tools/unpack.py extract ARCHIVE DIRECTORY
"""

from __future__ import annotations

import sys
from pathlib import Path

import libarchive


def main() -> int:
    command, archive = sys.argv[1], sys.argv[2]
    if command == "list":
        total = 0
        with libarchive.file_reader(archive) as entries:
            for entry in entries:
                total += entry.size or 0
                print(f"{entry.size or 0:12d}  {entry.pathname}")
        print(f"{total} bytes")
        return 0
    target = Path(sys.argv[3]).resolve()
    target.mkdir(parents=True, exist_ok=True)
    count = 0
    with libarchive.file_reader(archive) as entries:
        for entry in entries:
            path = (target / entry.pathname).resolve()
            # A file of the archive must stay inside the target directory.
            if target not in path.parents and path != target:
                raise SystemExit(f"the archive has a path outside the directory: {entry.pathname}")
            if entry.isdir:
                path.mkdir(parents=True, exist_ok=True)
                continue
            if not entry.isfile:
                continue  # no links, no devices
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("wb") as handle:
                for block in entry.get_blocks():
                    handle.write(block)
            count += 1
    print(f"{count} files in {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
