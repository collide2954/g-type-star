"""The mixer: tone, level, and space for each stem, then the master.

Each stem has a channel strip (`Strip`). The strips go into groups (buses):
the drums, the bass, and the music. The groups go into the mix. The master
gives the mix the loudness and the tone balance of the reference recordings
(see `research/measured/reference_recordings.csv`).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy import signal

from . import dsp, effects, loudness, reference

RATE = dsp.RATE


@dataclass(frozen=True)
class Strip:
    """The settings of one stem in the mix."""

    gain_db: float = 0.0
    # The group: drums (kick, snare, toms: with strong compression), cymbals (the
    # microphones of the cymbals: a part of the drum group, with no compression),
    # bass, music, or space (no group processing).
    bus: str = "music"
    pan: float = 0.0  # moves the stem between left (-1) and right (+1)
    width: float = 1.0
    # Filters: ("highpass", hertz), ("lowpass", hertz), ("bell", hertz, dB, quality),
    # ("low shelf", hertz, dB), ("high shelf", hertz, dB).
    eq: tuple[tuple, ...] = ()
    drive_db: float = 0.0  # saturation before the compressor
    compress: tuple[float, float, float, float] | None = None  # threshold, ratio, attack, release
    makeup_db: float = 0.0
    transient_db: float = 0.0  # louder starts of the sounds
    duck_db: float = 0.0  # the level goes down by this much at each stroke of the kick drum
    duck_release: float = 0.16
    room: float = 0.0  # share of the stem that goes to the short room
    plate: float = 0.0  # share that goes to the plate reverberation
    hall: float = 0.0  # share that goes to the long hall
    echo: float = 0.0  # share that goes to the echo
    chorus: float = 0.0


def filters(rows: tuple[tuple, ...]) -> list[np.ndarray]:
    """Change filter rows into filters of `dsp`."""
    result = []
    for kind, frequency, *rest in rows:
        if kind == "highpass":
            result.append(dsp.highpass(frequency, int(rest[0]) if rest else 2))
        elif kind == "lowpass":
            result.append(dsp.lowpass(frequency, int(rest[0]) if rest else 2))
        elif kind == "bell":
            result.append(dsp.peaking(frequency, rest[0], rest[1] if len(rest) > 1 else 1.0))
        elif kind == "low shelf":
            result.append(dsp.shelf(frequency, rest[0], high=False))
        elif kind == "high shelf":
            result.append(dsp.shelf(frequency, rest[0], high=True))
        else:
            raise ValueError(f"unknown filter {kind!r}")
    return result


def active(sound: np.ndarray, before: float = 0.3, after: float = 2.5) -> list[tuple[int, int]]:
    """Return the parts of a stem that have sound, as (first sample, last sample).

    Most stems are silent for most of the time. The mixer works only on the
    parts with sound, with some time before and after each part.
    """
    block = 4096
    count = len(sound) // block + 1
    padded = np.zeros(count * block, dtype=np.float32)
    padded[: len(sound)] = np.abs(sound).max(axis=1)
    loud = padded.reshape(count, block).max(axis=1) > 1e-5
    spans: list[tuple[int, int]] = []
    start = None
    for index, value in enumerate(list(loud) + [False]):
        if value and start is None:
            start = index
        elif not value and start is not None:
            first = max(0, start * block - int(before * RATE))
            last = min(len(sound), index * block + int(after * RATE))
            if spans and first <= spans[-1][1]:
                spans[-1] = (spans[-1][0], last)
            else:
                spans.append((first, last))
            start = None
    return spans


def channel(sound: np.ndarray, strip: Strip, kicks: np.ndarray | None = None) -> np.ndarray:
    """Apply a channel strip to a stem (two channels). Return the new stem."""
    result = np.zeros(sound.shape, dtype=np.float32)
    for first, last in active(sound):
        moved = None if kicks is None else kicks - first / RATE
        result[first:last] = _channel(sound[first:last], strip, moved)
    return result


def _channel(sound: np.ndarray, strip: Strip, kicks: np.ndarray | None) -> np.ndarray:
    out = sound.astype(np.float64)
    if strip.eq:
        out = effects.equalize(out, *filters(strip.eq))
    if strip.drive_db:
        out = effects.each(out, lambda part: effects.saturate(part, strip.drive_db))
    if strip.transient_db:
        out = effects.transient(out, strip.transient_db)
    if strip.compress is not None:
        threshold, ratio, attack, release = strip.compress
        out = effects.compress(out, threshold, ratio, attack, release, makeup_db=strip.makeup_db)
    if strip.chorus:
        out = effects.chorus(out, mix=strip.chorus)
    if strip.width != 1.0:
        out = effects.width(out, strip.width)
    if strip.pan:
        left = min(1.0, 1.0 - strip.pan)
        right = min(1.0, 1.0 + strip.pan)
        out = out * np.array([left, right])
    if strip.duck_db and kicks is not None and len(kicks):
        out = (
            out * effects.duck(len(out), kicks, strip.duck_db, release=strip.duck_release)[:, None]
        )
    return (out * dsp.db(strip.gain_db)).astype(np.float32)


@dataclass
class Mix:
    """The settings of the mix that are not for one stem."""

    strips: dict[str, Strip] = field(default_factory=dict)
    echo_seconds: float = 0.257  # a dotted eighth note at 175 quarter notes in a minute
    echo_feedback: float = 0.38
    room_seconds: float = 0.45
    plate_seconds: float = 1.7
    hall_seconds: float = 3.4
    room_db: float = -4.0
    plate_db: float = -7.0
    hall_db: float = -9.0
    echo_db: float = -8.0
    # The drum group: a part of it gets strong compression and comes back under the drums.
    # That part has no high frequencies: it must not make the cymbals louder.
    drum_crush_db: float = -7.0
    drum_crush_lowpass: float = 4500.0
    drum_drive_db: float = 3.0
    bus_gain_db: dict[str, float] = field(default_factory=dict)
    # The loudness of each group relative to the full mix, in LU. The mixer sets the
    # levels of the groups to these values. They are the mean values of the stems of
    # the six reference tracks (see research/measured/reference_stems.csv).
    balance: dict[str, float] | None = field(
        default_factory=lambda: {"drums": -4.2, "bass": -6.9, "music": -4.2}
    )


def balance_gains(groups: dict[str, np.ndarray], settings: Mix) -> dict[str, float]:
    """Return the gain of each group (dB) that gives the balance of the reference tracks.

    The music group stays; the other groups move.
    """
    gains = dict(settings.bus_gain_db)
    if not settings.balance:
        return gains
    measured = {
        name: loudness.integrated(loudness.block_power(groups[name].astype(np.float32)))
        for name in settings.balance
        if np.any(groups[name])
    }
    if "music" in measured and np.isfinite(measured["music"]):
        for name, value in measured.items():
            if name != "music" and np.isfinite(value):
                wanted = settings.balance[name] - settings.balance["music"]
                gains[name] = gains.get(name, 0.0) + wanted - (value - measured["music"])
    return gains


# The stems that the project gives to other people: the name of each stem of the mix
# that is not in the list goes to "synthesizers".
EXPORT_NAMES = {"gtr": "guitar", "keys": "keys", "tsax": "saxophone", "horns": "horns",
                "strings": "strings", "tape": "recorded-sounds"}  # fmt: skip


def export_name(name: str) -> str:
    """Return the name of the exported stem for a stem of the music or the space group."""
    return EXPORT_NAMES.get(name, "synthesizers")


def group_buses(
    stems: dict[str, np.ndarray],
    settings: Mix,
    kicks: np.ndarray | None = None,
    parts: dict[str, np.ndarray] | None = None,
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    """Apply the channel strips and make the groups. Return the groups and the effect sends.

    If `parts` is given, the function puts the stems of the music group and
    of the space group into it, each after its channel strip (see `export_name`).
    """
    length = max(len(stem) for stem in stems.values())
    buses = {name: np.zeros((length, 2), dtype=np.float32)
             for name in ("drums", "cymbals", "bass", "music", "space")}  # fmt: skip
    sends = {name: np.zeros((length, 2), dtype=np.float32)
             for name in ("room", "plate", "hall", "echo")}  # fmt: skip
    for name, stem in stems.items():
        strip = settings.strips.get(name, Strip())
        out = channel(stem, strip, kicks)
        buses[strip.bus][: len(out)] += out
        if parts is not None and strip.bus in ("music", "space"):
            target = parts.setdefault(export_name(name), np.zeros((length, 2), dtype=np.float32))
            target[: len(out)] += out
        for send in sends:
            share = getattr(strip, send)
            if share:
                sends[send][: len(out)] += out * np.float32(share)

    drums = buses["drums"]
    if np.any(drums):
        crushed = effects.compress(drums, -30.0, 8.0, 0.003, 0.09, makeup_db=14.0)
        crushed = effects.each(crushed, lambda part: effects.saturate(part, 6.0))
        crushed = signal.sosfilt(dsp.lowpass(settings.drum_crush_lowpass, 2), crushed, axis=0)
        drums = drums + crushed * dsp.db(settings.drum_crush_db)
        drums = effects.each(drums, lambda part: effects.saturate(part, settings.drum_drive_db))
    drums = (drums + buses["cymbals"]).astype(np.float32)
    groups = {"drums": drums, "bass": buses["bass"], "music": buses["music"],
              "space": buses["space"]}  # fmt: skip
    return groups, sends


def mix(
    stems: dict[str, np.ndarray],
    settings: Mix,
    kicks: np.ndarray | None = None,
    gains: dict[str, float] | None = None,
    parts: dict[str, np.ndarray] | None = None,
) -> tuple[np.ndarray, dict[str, float]]:
    """Mix the stems. Return the mix (two channels) before the master, and the group gains.

    `gains` are the gains of the groups in dB. If they are not given, the
    function finds them from the balance of the reference tracks.

    If `parts` is given, the function fills it with the stems for export:
    drums, bass, one stem for each instrument group of the music, the
    recorded sounds, and the reverberation. Their sum is the mix.
    """
    groups, sends = group_buses(stems, settings, kicks, parts)
    length = len(groups["drums"])
    if gains is None:
        gains = balance_gains(groups, settings)
    total = np.zeros((length, 2), dtype=np.float32)
    for name, bus in groups.items():
        total += bus * np.float32(dsp.db(gains.get(name, 0.0)))
    if parts is not None:
        music_gain = np.float32(dsp.db(gains.get("music", 0.0)))
        space_gain = np.float32(dsp.db(gains.get("space", 0.0)))
        for name in parts:
            parts[name] *= space_gain if name == "recorded-sounds" else music_gain
        for name in ("drums", "bass"):
            parts[name] = groups[name] * np.float32(dsp.db(gains.get(name, 0.0)))
        dry = total.copy()

    spaces = [
        ("room", effects.room(settings.room_seconds, 0.6, 0.004, 0.4, seed=3), settings.room_db),
        ("plate", effects.room(settings.plate_seconds, 0.75, 0.012, 1.0, seed=5),
         settings.plate_db),
        ("hall", effects.room(settings.hall_seconds, 0.4, 0.03, 1.0, seed=9), settings.hall_db),
    ]  # fmt: skip
    for name, response, level in spaces:
        if np.any(sends[name]):
            wet = effects.reverb(sends[name], response, tail=False)
            wet = signal.sosfilt(dsp.highpass(180.0, 2), wet, axis=0)
            total += (wet * dsp.db(level + gains.get("music", 0.0))).astype(np.float32)
    if np.any(sends["echo"]):
        echoes = effects.delay(sends["echo"], settings.echo_seconds, settings.echo_feedback)
        echoes = signal.sosfilt(dsp.highpass(250.0, 2), echoes, axis=0)
        total += (echoes[:length] * dsp.db(settings.echo_db)).astype(np.float32)
    if parts is not None:
        parts["reverb"] = total - dry
    return total, gains


TARGET_LUFS = -10.5  # the six reference tracks: -9.6 to -12.7 LUFS
CEILING_DB = -0.3


@dataclass
class MasterReport:
    seconds: float
    loudness_lufs: float
    loudness_range: float
    peak_db: float
    crest_db: float
    tone_change_db: tuple[float, float]
    limiter_drive_db: float


def master(
    sound: np.ndarray, target: float = TARGET_LUFS, tone: bool = True
) -> tuple[np.ndarray, MasterReport]:
    """Make the master from the mix: tone balance, glue, and loudness.

    1. Tone: the long-term balance of the mix goes to that of the reference tracks.
    2. Glue: a slow compressor with a small ratio on the full mix.
    3. Loudness: a soft clip and a limiter bring the mix to the target loudness.
       The function finds the input level of the limiter for which the result
       has the target loudness.
    """
    out = sound.astype(np.float32).copy()
    change = np.zeros(1)
    if tone and len(out) >= 16384:
        out, _centres, change = reference.match_tone_balance(out)
    out = effects.compress(out.astype(np.float64), -16.0, 1.8, 0.03, 0.25, knee_db=10.0)
    measured = loudness.integrated(loudness.block_power(out.astype(np.float32)))
    drive = target - measured
    final = out
    for _ in range(6):
        pushed = out * dsp.db(drive)
        final = effects.limit(effects.clip(pushed, -0.2, 0.25), CEILING_DB, 0.003, 0.06)
        now = loudness.integrated(loudness.block_power(final.astype(np.float32)))
        if abs(now - target) < 0.15:
            break
        drive += target - now
    final = final.astype(np.float32)
    power = loudness.block_power(final)
    spread, _gated = loudness.loudness_range(loudness.short_term(power))
    peak = float(np.max(np.abs(final)))
    report = MasterReport(
        seconds=len(final) / RATE,
        loudness_lufs=loudness.integrated(power),
        loudness_range=spread,
        peak_db=dsp.to_db(peak),
        crest_db=dsp.to_db(peak / max(dsp.rms(final), 1e-12)),
        tone_change_db=(float(change.min()), float(change.max())),
        limiter_drive_db=drive,
    )
    return final, report
