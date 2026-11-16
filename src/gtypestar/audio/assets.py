"""Download the free sound files that the audio of the work needs.

No sound file is in the repository. This module gets them from their
sources and keeps them in the directory `.cache`:

- a drum kit of DrumGizmo (`.cache/samples`),
- the sample banks of the bass guitar and of the electric piano,
- the public recordings of space and of space flight (`.cache/media`).

The module verifies the checksum of each media file after the download. If
a file changed at its source, the function stops with a message.

See docs/audio.md for the credits and the licences.
"""

from __future__ import annotations

import hashlib
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path

from . import banks, kit, tape


@dataclass(frozen=True)
class Media:
    """One recording of the part "Recorded Sounds"."""

    name: str  # the name of the file in the media directory
    url: str
    sha256: str
    credit: str


MEDIA = [
    Media(
        "sun-sonification.wav",
        "https://www.nasa.gov/wp-content/uploads/2018/07/sun_sonification.wav",
        "c2299c81ef4132c314b5a13e44af9fa6f8a4c4e733a2658df038291749f95bf8",
        "NASA, Sounds of the Sun (data: ESA and NASA, SOHO; A. Kosovichev, Stanford)",
    ),
    Media(
        "mercury3-548.mp3",
        "https://archive.org/download/Mercury3/548-AAG.mp3",
        "9f488c74064ce2b37b4c017d153edd742afca6dcd9a2a71e60cec432772127ed",
        "NASA, radio traffic of Mercury-Redstone 3 (1961), Internet Archive, public domain",
    ),
    Media(
        "voyager-heliosphere.wav",
        "https://space-audio.org/vger8204-darker-3.wav",
        "9ef3e70bad46bf2e8c04c26cd7f7d0c2f515c64f71883451b4e594cd382d8dbd",
        "NASA and The University of Iowa, https://space-audio.org/ (CC BY 4.0)",
    ),
    Media(
        "voyager-termination-shock.wav",
        "https://space-audio.org/voyager/termination-shock/vgertermshock4.wav",
        "4e0f2fe9158be96d1e492bb7eb231730d172373f11235171827a033d0073c15c",
        "NASA and The University of Iowa, https://space-audio.org/ (CC BY 4.0)",
    ),
    Media(
        "earth-chorus.mp3",
        "https://space-audio.org/sounds/EarthChorus/earchor.mp3",
        "370b8fd8b00951eefbfb690134bd7909d6a66ec0959f57725047131f25555789",
        "NASA and The University of Iowa, https://space-audio.org/ (CC BY 4.0)",
    ),
    Media(
        "cassini-saturn-radio.wav",
        "https://space-audio.org/cassini/SKR1/SKR-03-324.wav",
        "54b2e2a15edf1e65e5771c7d74422e9c158d0aa87b11fc5730c7a085d49ebdfb",
        "NASA and The University of Iowa, https://space-audio.org/ (CC BY 4.0)",
    ),
]


def _download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_suffix(path.suffix + ".part")
    subprocess.run(
        ["curl", "--fail", "--location", "--silent", "--show-error", "--retry", "3",
         "--user-agent", "g-type-star-build", "-o", str(part), url],
        check=True,
    )  # fmt: skip
    part.replace(path)


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def fetch_media() -> list[Path]:
    """Download the recordings that are not in the cache. Return the paths of all of them."""
    paths = []
    for item in MEDIA:
        path = tape.MEDIA_DIR / item.name
        if not path.exists():
            print(f"fetch: {item.name}")
            _download(item.url, path)
        found = checksum(path)
        if found != item.sha256:
            raise RuntimeError(
                f"{path}: the checksum is {found}, not {item.sha256}. The file at {item.url} "
                "changed, or the download is not complete."
            )
        paths.append(path)
    return paths


def fetch_kit(spec: kit.KitSpec | None = None) -> Path:
    """Download and unpack a drum kit, if it is not in the cache. Return its directory.

    The default is the kit of the work (CrocellKit: a download of 5.6 GB that
    becomes 9 GB). `kit.DRS` is smaller (2.8 GB, 4.3 GB unpacked).
    """
    spec = spec or kit.CROCELL
    folder = kit.SAMPLES_DIR / spec.folder
    if folder.exists():
        return folder
    top = kit.SAMPLES_DIR / Path(spec.folder).parts[0]
    archive = top / Path(spec.url).name
    if not archive.exists():
        print(f"fetch: {spec.name} ({spec.url})")
        _download(spec.url, archive)
    with zipfile.ZipFile(archive) as packed:
        packed.extractall(top)
    archive.unlink()
    if not folder.exists():
        raise RuntimeError(f"{archive}: the archive has no directory {spec.folder}")
    return folder


def fetch_all(small: bool = False) -> None:
    """Download all sound files. `small` gets the smaller drum kit (for a build server)."""
    fetch_media()
    fetch_kit(kit.DRS if small else kit.CROCELL)
    if banks.fetch_bass() is None:
        raise RuntimeError("the sample bank of the bass guitar did not download")
    if banks.fetch_rhodes() is None:
        raise RuntimeError("the sample bank of the electric piano did not download")
