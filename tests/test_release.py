"""Tests for the audio master in a release: the record, the stems file, and the download."""

from __future__ import annotations

import json
import subprocess
import zipfile
from pathlib import Path

import pytest

from gtypestar import release
from gtypestar.work import build


@pytest.fixture(scope="module")
def work():
    return build()


def test_the_record_says_for_which_music_a_master_is(work, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("GITHUB_SHA", "0123abc")
    record = release.write_record(work, tmp_path, "Synthesizer patches play.", stems=True)
    data = json.loads(record.read_text(encoding="utf-8"))
    assert data == {
        "music": release.music_key(work),
        "source": "Synthesizer patches play.",
        "commit": "0123abc",
        "stems": True,
    }
    assert len(data["music"]) == 64


def test_the_stems_go_into_one_file_with_no_compression(tmp_path) -> None:
    stems = tmp_path / "stems"
    stems.mkdir()
    assert release.pack_stems(stems, tmp_path / "audio" / release.STEMS) is None
    (stems / "drums.flac").write_bytes(b"fLaC" + bytes(1000))
    (stems / "bass.flac").write_bytes(b"fLaC" + bytes(500))
    (stems / "README.txt").write_text("The stems.\n", encoding="utf-8")
    (stems / ".drums.f32").write_bytes(bytes(10))  # a file of a render in progress
    packed = release.pack_stems(stems, tmp_path / "audio" / release.STEMS)
    assert packed == tmp_path / "audio" / release.STEMS
    with zipfile.ZipFile(packed) as file:
        assert file.namelist() == ["stems/bass.flac", "stems/drums.flac", "stems/README.txt"]
        assert {item.compress_type for item in file.infolist()} == {zipfile.ZIP_STORED}
        assert file.read("stems/drums.flac") == b"fLaC" + bytes(1000)


class _Release:
    """A release in memory, in the place of the program `gh`."""

    def __init__(self, files: dict[str, bytes] | None) -> None:
        self.files = files  # None: the release is not there
        self.calls: list[list[str]] = []

    def __call__(self, arguments: list[str], *, check: bool = True):
        self.calls.append(arguments)
        code = 0
        if arguments[:2] == ["release", "view"]:
            code = 0 if self.files is not None else 1
        elif arguments[:2] == ["release", "create"]:
            self.files = {}
        elif arguments[:2] == ["release", "upload"]:
            for name in arguments[3:-1]:
                self.files[Path(name).name] = Path(name).read_bytes()
        elif arguments[:2] == ["release", "download"]:
            name = arguments[arguments.index("--pattern") + 1]
            directory = Path(arguments[arguments.index("--dir") + 1])
            if self.files is None or name not in self.files:
                code = 1
            else:
                (directory / name).write_bytes(self.files[name])
        if code and check:
            raise subprocess.CalledProcessError(code, ["gh", *arguments])
        return subprocess.CompletedProcess(arguments, code, "", "")


def _master(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name in release.FILES:
        (directory / name).write_bytes(name.encode())


def test_a_master_goes_to_a_draft_release_and_comes_back(work, tmp_path, monkeypatch) -> None:
    store = _Release(None)
    monkeypatch.setattr(release, "_gh", store)
    home = tmp_path / "home" / "audio"
    stems = tmp_path / "home" / "stems"
    stems.mkdir(parents=True)
    (stems / "drums.flac").write_bytes(b"fLaC")
    with pytest.raises(FileNotFoundError):
        release.publish(work, home, "Muse Sounds play.", stems)
    _master(home)
    files = release.publish(work, home, "Muse Sounds play.", stems)
    assert [path.name for path in files] == [*release.FILES, release.STEMS, release.RECORD]
    # The release is a draft: it is not a publication.
    create = next(call for call in store.calls if call[:2] == ["release", "create"])
    assert "--draft" in create
    assert set(store.files) == {*release.FILES, release.STEMS, release.RECORD}

    server = tmp_path / "server" / "audio"
    assert release.fetch(work, server)
    assert {path.name for path in server.iterdir()} == {
        *release.FILES,
        release.STEMS,
        release.RECORD,
    }
    assert (server / release.FILES[0]).read_bytes() == release.FILES[0].encode()


def test_a_master_for_different_music_does_not_come(work, tmp_path, monkeypatch) -> None:
    record = json.dumps({"music": "different", "source": "", "commit": "", "stems": False})
    store = _Release({release.RECORD: record.encode(), release.FILES[0]: b"old"})
    monkeypatch.setattr(release, "_gh", store)
    assert not release.fetch(work, tmp_path / "audio")
    assert list((tmp_path / "audio").iterdir()) == []
    # No release: the same answer.
    monkeypatch.setattr(release, "_gh", _Release(None))
    assert not release.fetch(work, tmp_path / "audio")
