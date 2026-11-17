"""Download the free sound files that the audio of the work needs.

No sound file is in the repository. This module gets them from their
sources and keeps them in the directory `.cache`:

- a drum kit of DrumGizmo (`.cache/samples`),
- the sample banks of the bass guitar and of the electric piano,
- the recorded guitar and the models of its amplifiers,
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
        "apollo10-onboard.mp3",
        "https://apollojournals.org/afj/ap10fj/audio/a10o-1024751.mp3",
        "782052e7107a91436da48a309def59aebfb02f9bf47eab481beb1c53dd94c567",
        "NASA, voice recorder of the lunar module of Apollo 10 (1969), from the Apollo "
        "Flight Journal (clip: John Stoll, NASA Johnson), public domain",
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


# The models of the guitar amplifiers: files of the collection of the NAM community
# (https://github.com/pelennor2170/NAM_models, GPL 3.0). A model file has numbers only.
MODELS_URL = "https://raw.githubusercontent.com/pelennor2170/NAM_models/main/"
MODELS = {
    "Phillipe P Bugera6262-Lead-NoDrive-Cab-ESR0,009.nam":
        "881e0679bc2c5b05606f1f94e67ffcc8ab20d74cdf32f6326c09ef9562dcf96a",
    "Phillipe P Bug6262-Crunch-NoDrive-Cab-ESR0,004.nam":
        "b34b371d093faf5631e0e9c340e1600f95af043bb1e73cfd028ba775e228b1df",
    "Phillipe P Bug333-Clean-Cab-ESR0,007.nam":
        "684fc395e606ed46ab0af128189e02b0f769af872df9ec8bc7a046a340b12f95",
    "Phillipe P JVM-OD2-RD-NoDrive-Cab-ESR0,006.nam":
        "46d41f2dbde33d443ab4a2ef76d2782ea7609a778c4af0305f1f257f8cdcf4a9",
}  # fmt: skip
# The guitar library METAL-GTX of Unreal Instruments (a file on Google Drive, linked from
# https://unreal-instruments.wixsite.com/unreal-instruments/metal-gtx).
GUITAR_DRIVE_ID = "1FurY3_x_tog_56irX1VDNyRCUt5JD7bO"
GUITAR_SHA256 = "c5756f95fcc30ac680f6034bb2e54c636e67fd0b53b1d40babada7257e782e73"


def _verify(path: Path, wanted: str, source: str) -> None:
    found = checksum(path)
    if found != wanted:
        raise RuntimeError(
            f"{path}: the checksum is {found}, not {wanted}. The file at {source} changed, "
            "or the download is not complete."
        )


def fetch_models() -> list[Path]:
    """Download the amplifier models that are not in the cache. Return their paths."""
    from urllib.parse import quote

    from . import guitar

    paths = []
    for name, wanted in MODELS.items():
        path = guitar.MODELS_DIR / name.replace(" ", "_").replace(",", ".")
        if not path.exists():
            print(f"fetch: {name}")
            _download(MODELS_URL + quote(name), path)
        _verify(path, wanted, MODELS_URL)
        paths.append(path)
    return paths


def fetch_guitar() -> Path:
    """Download and unpack the guitar library, if it is not in the cache (1.3 GB).

    The library is a RAR archive. The function unpacks it with the libarchive
    library of the system, through the package `libarchive-c`:

        uv run --with libarchive-c gtypestar fetch
    """
    import re

    from . import guitar

    if (guitar.SAMPLES_DIR / "Sus_Down").exists():
        return guitar.SAMPLES_DIR
    try:
        import libarchive
    except ImportError as error:
        raise RuntimeError(
            "the guitar library is a RAR archive: run this command with the package "
            "libarchive-c (uv run --with libarchive-c gtypestar fetch)"
        ) from error
    top = guitar.SAMPLES_DIR.parents[1]
    archive = top / "METAL-GTX.rar"
    if not archive.exists():
        print("fetch: METAL-GTX (Google Drive)")
        page = archive.with_suffix(".page")
        _download(f"https://drive.google.com/uc?id={GUITAR_DRIVE_ID}&export=download", page)
        text = page.read_text(encoding="utf-8", errors="replace")
        action = re.search(r'action="([^"]+)"', text)
        fields = dict(re.findall(r'name="([^"]+)" value="([^"]*)"', text))
        if not action or "id" not in fields:
            raise RuntimeError("the download page of the guitar library has a new form")
        query = "&".join(f"{name}={value}" for name, value in fields.items())
        _download(f"{action.group(1)}?{query}", archive)
        page.unlink()
    _verify(archive, GUITAR_SHA256, "Google Drive")
    target = top.resolve()
    with libarchive.file_reader(str(archive)) as entries:
        for entry in entries:
            path = (target / entry.pathname).resolve()
            if target not in path.parents:
                raise RuntimeError(
                    f"the archive has a path outside its directory: {entry.pathname}"
                )
            if entry.isdir:
                path.mkdir(parents=True, exist_ok=True)
            elif entry.isfile:
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("wb") as handle:
                    for block in entry.get_blocks():
                        handle.write(block)
    archive.unlink()
    if not (guitar.SAMPLES_DIR / "Sus_Down").exists():
        raise RuntimeError("the archive of the guitar library has a new layout")
    return guitar.SAMPLES_DIR


def fetch_all(small: bool = False) -> None:
    """Download all sound files.

    `small` is for a build server: the smaller drum kit, and no recorded
    guitar (the string model plays the guitar part).
    """
    fetch_media()
    if not small:
        fetch_models()
        fetch_guitar()
    fetch_kit(kit.DRS if small else kit.CROCELL)
    if banks.fetch_bass() is None:
        raise RuntimeError("the sample bank of the bass guitar did not download")
    if banks.fetch_rhodes() is None:
        raise RuntimeError("the sample bank of the electric piano did not download")
