"""Command line interface: check the work, and build the audio, the score, and the video."""

from __future__ import annotations

import argparse
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

BUILD_DIR = Path("build")
NAME = "g-type-star"


def write_lilypond() -> list[Path]:
    """Write the LilyPond files of the score and the parts."""
    from .notation import lilypond
    from .work import build

    return lilypond.write_all(build(), BUILD_DIR / "ly")


def compile_pdf(path: Path, output: Path) -> None:
    """Compile one LilyPond file into a PDF file in the output directory."""
    output.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["lilypond", "-dno-point-and-click", "--loglevel=WARNING", "-o", str(output / path.stem),
         str(path)],
        capture_output=True,
        text=True,
        check=False,
    )  # fmt: skip
    if result.returncode != 0:
        raise RuntimeError(f"LilyPond failed for {path}:\n{result.stderr[-2000:]}")
    for line in result.stderr.splitlines():
        if "warning" in line and "compress" not in line:
            print(f"{path.name}: {line}")


def build_pdfs(*, parts: bool = True) -> None:
    """Build the score PDF and the part PDFs."""
    paths = write_lilypond()
    score = [path for path in paths if path.name == "score.ly"]
    others = [path for path in paths if path.name != "score.ly"] if parts else []
    compile_pdf(score[0], BUILD_DIR / "score")
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as pool:
        list(pool.map(lambda path: compile_pdf(path, BUILD_DIR / "parts"), others))


def write_audio(audio, directory: Path, name: str) -> list[Path]:
    """Write a master as FLAC and as MP3. Return the paths."""
    import soundfile

    from .audio import dsp

    directory.mkdir(parents=True, exist_ok=True)
    flac = directory / f"{name}.flac"
    soundfile.write(str(flac), audio, dsp.RATE, subtype="PCM_24")
    mp3 = directory / f"{name}.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(flac), "-codec:a", "libmp3lame",
         "-q:a", "1", str(mp3)],
        check=True,
    )  # fmt: skip
    return [flac, mp3]


def build_audio(
    bars: tuple[int, int] | None,
    muse: bool | None,
    name: str | None,
    export: bool = False,
    parts: tuple[int, int] | None = None,
) -> Path:
    """Render the audio master, or an excerpt of it. Return the path of the FLAC file.

    `export`: write the stems of the full work into the directory `build/stems` too.
    """
    from .audio import render
    from .work import build

    export_to = BUILD_DIR / "stems" if export and bars is None else None
    work = build()
    audio, report = render.render(work, bars, muse=muse, export_to=export_to, only=parts)
    if export_to is not None:
        print(f"stems: {export_to}")
    name = name or (NAME if bars is None else f"excerpt-{bars[0]}-{bars[1]}")
    paths = write_audio(audio, BUILD_DIR / "audio", name)
    for path in paths:
        print(f"audio: {path}")
    if name == NAME and bars is None and parts is None:
        # The master of the work: a text says for which music it is and which sounds
        # play it, and the stems are in one file (as in the release: see `release.py`).
        from . import release

        packed = release.pack_stems(export_to, paths[0].parent / release.STEMS) if export else None
        release.write_record(work, paths[0].parent, render.sources(muse), packed is not None)
    print(
        f"{report.seconds / 60:.2f} minutes, {report.loudness_lufs:.1f} LUFS, loudness range "
        f"{report.loudness_range:.1f} LU, peak {report.peak_db:.1f} dB, crest factor "
        f"{report.crest_db:.1f} dB"
    )
    compare(paths[0])
    return paths[0]


def compare(path: Path) -> None:
    """Compare an audio file with the reference tracks: loudness, stereo width, tone balance."""
    from .audio import reference

    measured = reference.measure(reference.load_stereo(path))
    centres, mean, lowest, highest = reference.target_balance()
    print(
        f"compare: {measured.loudness_lufs:.1f} LUFS (references -12.7 to -9.6), loudness range "
        f"{measured.loudness_range:.1f} LU (4.6 to 12.6), crest factor {measured.crest_db:.1f} dB "
        f"(11.7 to 14.6), correlation {measured.correlation:.2f} (0.71 to 0.80), side level "
        f"{measured.side_db:.1f} dB (-9.6 to -7.7)"
    )
    outside = [
        f"{centre:.0f} Hz {value - (high if value > high else low):+.1f} dB"
        for centre, value, low, high in zip(centres, measured.balance, lowest, highest, strict=True)
        if 28.0 < centre < 16500.0 and (value > high + 1.0 or value < low - 1.0)
    ]
    text = ", ".join(outside) if outside else "all bands from 31 Hz to 16 kHz are in the range"
    print(f"compare: tone balance: {text}")
    del mean


def write_stems(bars: tuple[int, int] | None, muse: bool | None, show_only: bool) -> None:
    """Render the stems of the work or of some bars. Write them, or only show their loudness."""
    import numpy as np
    import soundfile

    from .audio import dsp, loudness, render
    from .work import build

    work = build()
    parts = [bars] if bars is not None else render.chunks(work)
    directory = BUILD_DIR / "stems"
    for part in parts:
        stems, _kicks, _seconds = render.render_stems(work, part, muse=muse)
        for name, sound in sorted(stems.items()):
            level = loudness.integrated(loudness.block_power(sound.astype(np.float32)))
            peak = dsp.to_db(float(np.abs(sound).max()))
            print(f"bars {part[0]}-{part[1]}: {name:16s} {level:7.1f} LUFS  peak {peak:6.1f} dB")
            if not show_only:
                target = directory / f"bars-{part[0]:03d}-{part[1]:03d}"
                target.mkdir(parents=True, exist_ok=True)
                soundfile.write(str(target / f"{name}.flac"), sound, dsp.RATE, subtype="PCM_24")


def check_work() -> int:
    """Find music that a player cannot play. Return the number of problems."""
    from .compose.check import check
    from .work import build

    work = build()
    problems = check(work)
    for problem in problems:
        print(problem)
    seconds = work.structure.duration_seconds
    print(f"{len(work.structure.bars)} bars, {seconds / 60:.2f} minutes, {len(problems)} problems")
    return len(problems)


def build_video(mobile: bool = False) -> None:
    """Render the score video. The audio master must exist.

    If `mobile` is true, the video is for a telephone (1080 x 1920).
    """
    from .video import pages, render
    from .work import build

    work = build()
    audio = BUILD_DIR / "audio" / f"{NAME}.flac"
    if mobile:
        screens = pages.build_pages(
            work, BUILD_DIR / "video" / "pages-mobile", width_px=1080, mobile=True
        )
        output = BUILD_DIR / "video" / f"{NAME}-mobile.mp4"
        path = render.render(work, screens, audio, output, width=1080, height=1920, mobile=True)
    else:
        screens = pages.build_pages(work, BUILD_DIR / "video" / "pages")
        path = render.render(work, screens, audio, BUILD_DIR / "video" / f"{NAME}.mp4")
    print(f"video: {path}")


def show_stats() -> None:
    """Print the numbers of the work as a table."""
    from .compose.stats import measure
    from .work import build

    for name, value in measure(build()).rows():
        print(f"{name:62s} {value}")


def write_midi() -> None:
    """Write the performance of the work as a MIDI file."""
    from .perform import midi
    from .work import build

    print(f"midi: {midi.write(build(), BUILD_DIR / 'midi' / f'{NAME}.mid')}")


def update_documents() -> None:
    """Write the bar numbers, the times, and the measured values of the work into the documents."""
    from . import documents
    from .work import build

    changed = documents.update_files(build())
    for path in changed:
        print(f"docs: updated {path}")
    if not changed:
        print("docs: the documents are up to date")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gtypestar", description="Build G-Type Star.")
    parser.add_argument(
        "command",
        choices=["check", "stats", "ly", "score", "parts", "audio", "stems", "levels", "compare",
                 "midi", "video", "docs", "fetch", "fetch-audio", "publish-audio", "all"],
    )  # fmt: skip
    parser.add_argument("file", nargs="?", help="an audio file (command: compare)")
    parser.add_argument("--bars", metavar="FIRST-LAST", help="render only these bars")
    parser.add_argument("--name", help="the name of the audio file (command: audio)")
    parser.add_argument(
        "--no-muse",
        action="store_true",
        help="do not use MuseScore: synthesizer patches play the wind and string parts",
    )
    parser.add_argument(
        "--parts",
        metavar="FIRST-LAST",
        help="a test of the full render: only its parts inside these bars (command: audio)",
    )
    parser.add_argument(
        "--export-stems",
        action="store_true",
        help="write the stems of the full work into build/stems (command: audio)",
    )
    parser.add_argument(
        "--small",
        action="store_true",
        help="get the smaller drum kit, for a build server (command: fetch)",
    )
    parser.add_argument(
        "--mobile",
        action="store_true",
        help="make the video for a telephone, 1080 x 1920 (command: video)",
    )
    args = parser.parse_args(argv)
    bars = None
    if args.bars:
        first, _, last = args.bars.partition("-")
        bars = (int(first), int(last or first))
    muse = False if args.no_muse else None
    if args.command == "check":
        return 1 if check_work() else 0
    if args.command == "fetch":
        from .audio import assets

        assets.fetch_all(small=args.small)
        return 0
    if args.command in ("fetch-audio", "publish-audio"):
        from . import release
        from .work import build

        directory = BUILD_DIR / "audio"
        if args.command == "fetch-audio":
            # The exit code 1 says: the release has no master for this music.
            return 0 if release.fetch(build(), directory) else 1
        from .audio import render

        files = release.publish(build(), directory, render.sources(), BUILD_DIR / "stems")
        names = ", ".join(path.name for path in files)
        print(f"publish-audio: the draft release '{release.TAG}' has the new master ({names})")
        return 0
    if args.command == "stats":
        show_stats()
    elif args.command == "docs":
        update_documents()
    elif args.command == "ly":
        for path in write_lilypond():
            print(path)
    elif args.command == "score":
        build_pdfs(parts=False)
    elif args.command == "parts":
        build_pdfs(parts=True)
    elif args.command == "audio":
        parts = None
        if args.parts:
            first, _, last = args.parts.partition("-")
            parts = (int(first), int(last))
        build_audio(bars, muse, args.name, args.export_stems, parts)
    elif args.command in ("stems", "levels"):
        write_stems(bars, muse, show_only=args.command == "levels")
    elif args.command == "compare":
        compare(Path(args.file or BUILD_DIR / "audio" / f"{NAME}.flac"))
    elif args.command == "midi":
        write_midi()
    elif args.command == "video":
        build_video(args.mobile)
    else:
        build_pdfs(parts=True)
        build_audio(None, muse, None, export=True)
        write_midi()
        build_video()
        build_video(mobile=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
