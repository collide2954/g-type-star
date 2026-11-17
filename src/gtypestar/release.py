"""Keep the audio master in a GitHub release.

The saxophone, the horns and the strings of the master are Muse Sounds. A
build server cannot make this master: it cannot install Muse Sounds. The
computer of the composer makes the master and the stems and puts them in
the release `audio`. The build server gets them from that release, if they
are for the music of the present commit. If not, the build server makes
the audio itself: synthesizer patches play the wind and string parts, and
the drum kit is a smaller kit.

The release `audio` is a draft: only persons and builds with the right to
write to the repository can see it. It is a place where the build server
finds the files. It is not a publication of the work.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import zipfile
from pathlib import Path

from .notation import music
from .notation.work import Work

TAG = "audio"
FILES = ("g-type-star.flac", "g-type-star.mp3")
STEMS = "g-type-star-stems.zip"
RECORD = "audio.json"
NOTES = (
    "The audio master and the stems of the work, made on the computer of the composer "
    "with MuseScore Studio and Muse Sounds. A build server cannot make these files. "
    "The builds of the repository use them."
)


def music_key(work: Work) -> str:
    """Return a checksum of the music: all notes, the tempo plan, and the recorded sounds."""
    digest = hashlib.sha256()
    for player in work.orchestra.players:
        digest.update(player.id.encode())
        digest.update(music.body_to_lilypond(work.music_of(player.id)).encode())
    for point in work.structure.tempo_points:
        digest.update(f"{point.position}|{point.bpm}|{point.glide}".encode())
    for bar in work.structure.bars:
        digest.update(f"{bar.numerator}/{bar.denominator}".encode())
    # The cues of the recorded sounds and the changes of the recording are music too.
    for name in ("cues", "edits"):
        digest.update(repr(work.extras.get(name, [])).encode())
    return digest.hexdigest()


def commit() -> str:
    """Return the name of the present commit, or "" if it is not known."""
    if os.environ.get("GITHUB_SHA"):
        return os.environ["GITHUB_SHA"]
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def write_record(work: Work, directory: Path, source: str, stems: bool) -> Path:
    """Write the text that says for which music an audio master is, and where it is from."""
    directory.mkdir(parents=True, exist_ok=True)
    record = directory / RECORD
    data = {"music": music_key(work), "source": source, "commit": commit(), "stems": stems}
    record.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return record


def pack_stems(stems: Path, target: Path) -> Path | None:
    """Put the stems of a directory in one ZIP file. Return its path, or None if the
    directory has no stems.

    The stems are FLAC files: the ZIP file does not compress them again.
    """
    files = sorted(stems.glob("*.flac"))
    if not files:
        return None
    files += sorted(stems.glob("*.txt"))
    target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_suffix(".part")
    with zipfile.ZipFile(part, "w", compression=zipfile.ZIP_STORED) as packed:
        for path in files:
            packed.write(path, f"stems/{path.name}")
    part.replace(target)
    return target


def _gh(arguments: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["gh", *arguments], capture_output=True, text=True, check=check)


def publish(work: Work, directory: Path, source: str, stems: Path | None = None) -> list[Path]:
    """Put the audio master of `directory` in the release, with the checksum of the music.

    With `stems` (the directory of the stems), the stems go there too, as one
    ZIP file. If the release is not there, the function makes it as a draft.
    Return the files of the release.
    """
    files = [directory / name for name in FILES]
    missing = [str(path) for path in files if not path.exists()]
    if missing:
        raise FileNotFoundError(f"no audio master: {', '.join(missing)}")
    packed = pack_stems(stems, directory / STEMS) if stems is not None else None
    if packed is not None:
        files.append(packed)
    files.append(write_record(work, directory, source, packed is not None))
    if _gh(["release", "view", TAG], check=False).returncode != 0:
        _gh(["release", "create", TAG, "--draft", "--title", "Audio master", "--notes", NOTES])
    _gh(["release", "upload", TAG, *(str(path) for path in files), "--clobber"])
    return files


def fetch(work: Work, directory: Path) -> bool:
    """Get the audio master from the release. Return false if it is not for this music.

    The stems come too, as the file `STEMS` in `directory`, if the release has them.
    """
    directory.mkdir(parents=True, exist_ok=True)

    def download(name: str) -> str:
        """Get one file of the release. Return "" or the words of the error."""
        arguments = ["release", "download", TAG, "--pattern", name, "--dir", str(directory),
                     "--clobber"]  # fmt: skip
        result = _gh(arguments, check=False)
        return "" if result.returncode == 0 else (result.stderr.strip() or "no such file")

    record = directory / RECORD
    record.unlink(missing_ok=True)
    error = download(RECORD)
    if error or not record.exists():
        print(f"fetch-audio: the release '{TAG}' has no audio master ({error})")
        return False
    data = json.loads(record.read_text(encoding="utf-8"))
    if data.get("music") != music_key(work):
        print("fetch-audio: the audio master of the release is for different music")
        record.unlink()
        return False
    for name in (*FILES, *([STEMS] if data.get("stems") else [])):
        error = download(name)
        if error:
            raise RuntimeError(f"fetch-audio: {name} did not come from the release: {error}")
    print(f"fetch-audio: got the audio master from the release '{TAG}' ({data.get('source')})")
    return True
