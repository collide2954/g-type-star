"""The band: make the sound of each player from the events of the performance.

Each function gets the events of one player (times in seconds) and returns
a signal with two channels that starts at the start of the work (or of the
excerpt). The mixer (`console.py`) gets these stems.

Sources of sound:

- Synthesizers, chip sounds, voice pad, drum machine: code (`synth.py`, `drumsynth.py`).
- Guitar and bass guitar: a string model through an amplifier (`amp.py`).
- Drum kit: samples of a real kit with many microphones (`kit.py`).
- Saxophones, brass, strings, electric piano: MuseScore with Muse Sounds, if
  the computer has them. If not, synthesizer patches play these parts.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

import numpy as np
from scipy import signal

from ..perform.feel import Event
from . import (
    amp,
    banks,
    drumsynth,
    dsp,
    dubstep,
    effects,
    guitar,
    kernels,
    patches,
    sfzguitar,
    synth,
)

RATE = dsp.RATE
CACHE_DIR = Path(".cache/render")
VERSION = 13  # a change of this number makes all kept stems invalid
BASS = 2  # a change of the code that plays the bass guitar: a new number here
PHRASE_GAP = 0.03  # a line with a rest longer than this starts a new phrase (seconds)


class Canvas:
    """A signal with two channels to which sounds are added at given times."""

    def __init__(self, seconds: float) -> None:
        self.data = np.zeros((int(seconds * RATE) + RATE, 2), dtype=np.float32)

    def add(self, start: float, sound: np.ndarray, gain: float = 1.0) -> None:
        first = int(round(start * RATE))
        if first < 0:
            sound = sound[-first:]
            first = 0
        if first >= len(self.data) or len(sound) == 0:
            return
        if sound.ndim == 1:
            sound = effects.stereo(sound)
        last = min(len(self.data), first + len(sound))
        self.data[first:last] += (sound[: last - first] * gain).astype(np.float32)


def cached(name: str, events: list[Event], extra: object, make) -> np.ndarray:
    """Return a stem from the cache, or make it and keep it.

    The key of the cache has all values that change the sound: the events,
    the settings, and the version of the code.
    """
    digest = hashlib.sha1(repr((VERSION, name, extra)).encode())  # noqa: S324 (not for security)
    for event in events:
        note = event.note
        digest.update(
            repr(
                (round(event.start, 5), round(event.seconds, 5), note.midi, round(event.level, 4),
                 round(event.level_end, 4), note.instrument, note.legato, note.accent,
                 sorted(note.articulations), note.glissando, note.harmonic, note.tremolo,
                 note.grace, note.state)
            ).encode()
        )  # fmt: skip
    path = CACHE_DIR / f"{name.replace(' ', '-')}-{digest.hexdigest()[:16]}.npy"
    if path.exists():
        return np.load(path)
    sound = make()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    np.save(path, sound.astype(np.float32))
    return sound


def sounding(event: Event) -> float:
    """Return how long the player holds the note, in seconds."""
    marks = event.note.articulations
    if "staccatissimo" in marks:
        return max(0.03, 0.3 * event.seconds)
    if "staccato" in marks:
        return max(0.04, 0.5 * event.seconds)
    if "portato" in marks:
        return 0.8 * event.seconds
    if event.note.legato or "tenuto" in marks:
        return event.seconds
    return max(0.04, event.seconds - min(0.03, 0.08 * event.seconds))


def accent_level(event: Event) -> tuple[float, float]:
    """Return the loudness of the event with its accent."""
    more = event.note.accent
    return min(1.0, event.level + more), min(1.0, event.level_end + 0.5 * more)


# ----------------------------------------------------------------------------
# Synthesizers
# ----------------------------------------------------------------------------


def render_patch(events: list[Event], seconds: float, player: str) -> np.ndarray:
    """Play the events of a synthesizer player. Each event names its patch."""
    canvas = Canvas(seconds)
    by_patch: dict[str, list[Event]] = {}
    # The bass sounds of dubstep take turns from note to note above one sub tone: one
    # function plays all of them.
    heavy = [event for event in events if event.note.instrument in dubstep.SOUNDS]
    if heavy:
        canvas.add(0.0, dubstep.render(heavy, seconds, player))
    for event in events:
        if event.note.instrument not in dubstep.SOUNDS:
            by_patch.setdefault(event.note.instrument, []).append(event)
    for name, group in by_patch.items():
        if name in patches.FM:
            patch = patches.FM[name]
            for number, event in enumerate(group):
                level, _end = accent_level(event)
                sound = synth.render_fm(patch, event.midi, sounding(event), level,
                                        seed=(player, number))  # fmt: skip
                canvas.add(event.start, sound)
        elif name in patches.SUBTRACTIVE:
            patch = patches.SUBTRACTIVE[name]
            if patch.glide > 0:
                _lines(canvas, patch, group, player)
            else:
                for number, event in enumerate(group):
                    level, level_end = accent_level(event)
                    sound = synth.render_note(patch, event.midi, sounding(event), level, level_end,
                                              seed=(player, number))  # fmt: skip
                    canvas.add(event.start, sound)
        elif name.startswith("chip"):
            canvas.add(0.0, chip(group, seconds, name))
        elif name == "voice pad":
            canvas.add(0.0, voice_pad(group, seconds, player))
        else:
            raise KeyError(f"no synthesizer patch with the name {name!r}")
    return canvas.data


def _lines(canvas: Canvas, patch: synth.Patch, events: list[Event], player: str) -> None:
    """Play a patch with slides: one voice, in phrases."""
    events = sorted(events, key=lambda event: event.start)
    phrase: list[Event] = []

    def flush() -> None:
        if not phrase:
            return
        origin = phrase[0].start
        notes = []
        for number, event in enumerate(phrase):
            level, level_end = accent_level(event)
            following = phrase[number + 1] if number + 1 < len(phrase) else None
            length = sounding(event)
            if following is not None and following.note.legato:
                length = following.start - event.start  # no gap before a legato note
            bend: tuple[float, ...] = ()
            if event.note.glissando and following is not None:
                span = following.midi - event.midi
                bend = (0.0, 0.0, 0.3 * span, span)
            notes.append(
                synth.LineNote(event.start - origin, max(0.02, length), event.midi, level,
                               level_end, legato=number > 0 and event.note.legato,
                               vibrato=0.0 if event.seconds < 0.25 else 1.0, bend=bend)
            )  # fmt: skip
        canvas.add(origin, synth.render_line(patch, notes, seed=(player, round(origin, 3))))
        phrase.clear()

    for event in events:
        if phrase:
            last = phrase[-1]
            if event.start - (last.start + last.seconds) > PHRASE_GAP and not event.note.legato:
                flush()
        phrase.append(event)
    flush()


VOWELS = {"a": (850.0, 1610.0, 2700.0), "o": (360.0, 640.0, 2500.0), "u": (250.0, 595.0, 2400.0),
          "e": (390.0, 2300.0, 2900.0), "i": (240.0, 2400.0, 3100.0)}  # fmt: skip
CHIP_WIDTH = {"chip pulse": 0.5, "chip pulse 25": 0.25, "chip pulse 12": 0.125}
FRAME = RATE // 60  # an old game console changes its sound 60 times in a second


def chip(events: list[Event], seconds: float, name: str) -> np.ndarray:
    """The sound channels of an old game console: pulse waves and a stepped triangle.

    The loudness has 16 steps and changes 60 times in a second. A note with
    the mark "tremolo" is an arpeggio... of its own pitch and the octave.
    """
    canvas = Canvas(seconds)
    table = np.concatenate([np.arange(16), np.arange(15, -1, -1)]) / 7.5 - 1.0
    for event in events:
        length = sounding(event)
        total = int((length + 0.03) * RATE)
        time = np.arange(total) / RATE
        frames = np.arange(total) // FRAME
        pitch = np.full(total, event.midi)
        # Vibrato in steps, after a short delay: the sound of game music.
        wobble = np.where(time > 0.18, np.round(2.0 * np.sin(2 * np.pi * 6.0 * time)) * 0.12, 0.0)
        pitch = pitch + (wobble if length > 0.3 else 0.0)
        if event.note.tremolo:
            pitch = pitch + 12.0 * ((frames // 2) % 2)
        frequency = synth.hertz(pitch)
        level, _end = accent_level(event)
        if name == "chip triangle":
            wave = kernels.stepped(frequency, table, float(RATE)) * 0.9
            volume = np.where(time < length, 1.0, 0.0)
        else:
            wave = kernels.pulse(frequency, np.full(total, CHIP_WIDTH[name]), float(RATE), 0.0)
            start = np.round(level * 15.0)
            decay = np.maximum(start - frames // 4, np.round(0.55 * start))
            volume = np.where(time < length, decay, 0.0) / 15.0
        sound = wave * volume * 0.16
        sound[:24] *= np.linspace(0.0, 1.0, min(24, total))[: len(sound[:24])]
        canvas.add(event.start, effects.stereo(sound))
    return canvas.data


def voice_pad(events: list[Event], seconds: float, player: str) -> np.ndarray:
    """A choir of a synthesizer: sawtooth waves through the resonances of a vowel.

    The vowel changes slowly from "a" to "o" and back.
    """
    canvas = Canvas(seconds)
    source = synth.Patch(
        "voice source", (synth.Osc("saw", voices=3, spread=16.0), synth.Osc("pulse", width=0.3,
                                                                              level=0.4)),
        noise=0.02, filter="none", amplitude=synth.Envelope(0.25, 0.8, 0.9, 0.7), stereo=0.8,
        vibrato_cents=10.0, vibrato_delay=0.5,
    )  # fmt: skip
    for number, event in enumerate(events):
        level, level_end = accent_level(event)
        raw = synth.render_note(source, event.midi, sounding(event), level, level_end,
                                seed=(player, number)).astype(np.float64)  # fmt: skip
        time = np.arange(len(raw)) / RATE
        morph = 0.5 + 0.5 * np.sin(2 * np.pi * 0.13 * (time + event.start))
        out = np.zeros_like(raw)
        for index in range(3):
            centre = VOWELS["a"][index] * (1.0 - morph) + VOWELS["o"][index] * morph
            quality = np.full(len(raw), 7.0 if index < 2 else 5.0)
            for channel in range(2):
                band = kernels.state_variable(raw[:, channel], centre, quality, float(RATE), 1)
                out[:, channel] += band * (1.0, 0.7, 0.35)[index]
        canvas.add(event.start, out * 2.2)
    return canvas.data


# ----------------------------------------------------------------------------
# Drum machine
# ----------------------------------------------------------------------------


def render_machine(events: list[Event], seconds: float) -> np.ndarray:
    """Play the electronic percussion."""
    canvas = Canvas(seconds)
    for number, event in enumerate(events):
        midi = int(event.midi)
        level, _end = accent_level(event)
        length = event.seconds
        if midi == 36:
            sound = drumsynth.kick(level, number)
        elif midi == 35:
            sound = drumsynth.hard_kick(level, number) * 1.5
        elif midi == 40:
            sound = drumsynth.heavy_snare(level, number) * 1.8
        elif midi == 41:
            # In a roll with a crescendo, the pitch of the drum rises with the loudness.
            sound = drumsynth.roll_snare(level, number, pitch=140.0 * 2.0 ** (1.5 * level))
        elif midi == 32:
            sound = drumsynth.reverse_cymbal(max(0.2, length), level, number)
        elif midi == 38:
            sound = drumsynth.snare(level, number, pitch=205.0, decay=0.14)
        elif midi == 39:
            sound = drumsynth.clap(level, number)
        elif midi == 37:
            sound = drumsynth.rim(level, number)
        elif midi == 42:
            sound = drumsynth.hat(level, number, decay=0.035)
        elif midi == 46:
            sound = drumsynth.hat(level, number, decay=min(0.45, max(0.1, length * 0.6)))
        elif midi == 45:
            sound = drumsynth.tom(level, number, pitch=92.0)
        elif midi == 56:
            sound = drumsynth.zap(level, number)
        elif midi == 27:
            sound = drumsynth.sub_drop(level, max(0.6, length))
        elif midi == 28:
            sound = drumsynth.riser(max(0.3, length), level, number)
        elif midi == 29:
            sound = drumsynth.downlifter(max(0.3, length), level, number)
        elif midi == 30:
            sound = drumsynth.impact(level, number)
        elif midi == 31:
            random = np.random.default_rng(number)
            burst = random.normal(0.0, 0.25 * level, int(max(0.02, length) * RATE))
            sound = burst * np.exp(-np.arange(len(burst)) / (0.5 * len(burst) + 1.0))
        else:
            continue
        # Wide sounds for the long effects; the drums stay in the centre.
        if sound.ndim == 2:
            canvas.add(event.start, sound)
        elif midi in (28, 29, 31):
            delayed = np.concatenate([np.zeros(211), sound[:-211]]) if len(sound) > 211 else sound
            canvas.add(event.start, np.stack([sound, delayed], axis=1))
        else:
            canvas.add(event.start, effects.stereo(sound) * 1.41)
    return canvas.data


# ----------------------------------------------------------------------------
# Guitar and bass guitar
# ----------------------------------------------------------------------------

AMPS = {"clean": amp.CLEAN, "crunch": amp.CRUNCH, "high gain": amp.HIGH_GAIN, "lead": amp.LEAD}
LEAD_ECHO_SECONDS = 0.257  # an eighth note with a dot at 175 quarter notes in a minute
LEAD_ECHO_DB = -15.0


def _string_notes(events: list[Event], shift: float = 0.0, seed: int = 0) -> list[amp.StringNote]:
    """Change events into notes of the string model."""
    random = np.random.default_rng(seed)
    notes = []
    ordered = sorted(events, key=lambda event: event.start)
    for number, event in enumerate(ordered):
        note = event.note
        level, _end = accent_level(event)
        muted = note.get("mute") == "palm"
        following = ordered[number + 1] if number + 1 < len(ordered) else None
        bend: tuple[float, ...] = ()
        if note.glissando and following is not None:
            span = following.midi - event.midi
            bend = (0.0, 0.0, 0.4 * span, span)
        length = sounding(event)
        if note.get("ring") == "on":
            length = max(length, 1.6)
        notes.append(
            amp.StringNote(
                start=event.start + shift + (float(random.normal(0.0, 0.004)) if seed else 0.0),
                seconds=length,
                midi=event.midi,
                level=float(np.clip(level + (random.normal(0.0, 0.03) if seed else 0.0), 0.05, 1)),
                mute=0.88 if muted else 0.0,
                slide_from=event.midi - 1.0 if note.grace else None,
                bend=bend,
                vibrato=18.0 if (event.seconds > 0.4 and not muted) else 0.0,
                hammer=note.legato or note.get("attack") == "tap",
                harmonic=note.harmonic,
                dead="staccatissimo" in note.articulations and muted,
            )
        )
    return notes


def _strokes(events: list[Event], seed: int = 0) -> list[guitar.Stroke]:
    """Change events into notes of the recorded guitar. `seed` gives one performance."""
    return [
        guitar.Stroke(
            start=note.start,
            seconds=note.seconds,
            midi=note.midi,
            level=note.level,
            mute=note.mute > 0.5,
            hammer=note.hammer,
            dead=note.dead,
            slide_from=note.slide_from,
            bend=note.bend,
            vibrato=note.vibrato,
        )
        for note in _string_notes(events, seed=seed)
    ]


# The distortion of an amplifier is a compressor: a soft stroke is nearly as loud as a
# hard stroke after it. A fader after the amplifier follows the written loudness, as the
# volume control of the player (or the engineer at the console) does. The numbers are
# the range of the fader in dB between the loudness values 0 and 1, for each tone. The
# lead tone has no soft passage, and a clean guitar has its loudness from the strokes.
FADER_DB = {"high gain": 24.0, "crunch": 10.0, "lead": 0.0, "clean": 0.0}
FADER_FULL = 0.83  # the loudness (fortissimo) at which the fader is at 0 dB


def fader(events: list[Event], count: int, range_db: float) -> np.ndarray:
    """Return the gain of a fader that follows the written loudness, for `count` samples.

    The loudness of a note goes from its start to its end: a hairpin on a
    long note is a move of the fader. Between two notes the fader stays
    where it is.
    """
    if not range_db or not events:
        return np.ones(count, dtype=np.float32)
    step = RATE // 100
    size = count // step + 2
    curve = np.full(size, np.nan)
    for event in sorted(events, key=lambda item: item.start):
        first = int(event.start * RATE) // step
        last = int((event.start + event.seconds) * RATE) // step
        if first >= size or last < 0:
            continue
        first, last = max(first, 0), min(max(last, first + 1), size)
        curve[first:last] = np.linspace(event.level, event.level_end, last - first)
    known = np.flatnonzero(~np.isnan(curve))
    if len(known) == 0:
        return np.ones(count, dtype=np.float32)
    places = np.maximum.accumulate(np.where(np.isnan(curve), 0, np.arange(size)))
    places[: known[0]] = known[0]
    curve = curve[places]
    curve = np.convolve(np.pad(curve, 2, mode="edge"), np.ones(5) / 5.0, mode="valid")
    gain_db = np.minimum(range_db * (curve - FADER_FULL), 3.0)
    samples = np.interp(np.arange(count), np.arange(size) * step, gain_db)
    return (10.0 ** (samples / 20.0)).astype(np.float32)


def guitar_direct(strokes: list[guitar.Stroke], seconds: float, side: int, seed: int) -> np.ndarray:
    """Return the direct signal of one performance of the guitar, from the player of the work.

    The player is the program of the library in a sampler (`sfzguitar.py`),
    if the sampler is on the computer. If not, it is the player of
    `guitar.py`.
    """
    player = sfzguitar if sfzguitar.selected() else guitar
    return player.direct(strokes, seconds, side, seed)


def _take(seed: int) -> int:
    """Return the seed for the small differences of time and loudness of one performance.

    The sampler does not get such differences from the code (the seed 0):
    the recordings of its program have their own.
    """
    return 0 if sfzguitar.selected() else seed


def _clean_level(wet: np.ndarray) -> np.ndarray:
    """A clean guitar has large peaks: a compressor makes its level even."""
    both = np.stack([wet, wet], axis=1)
    return effects.compress(both, -20.0, 3.0, 0.015, 0.12)[:, 0]


def render_guitar(events: list[Event], seconds: float) -> np.ndarray:
    """Play the guitar. The rhythm tones are played two times, left and right.

    Two takes of the same part, one on each side, are the usual sound of
    heavy rhythm guitars: the small differences of the takes make the width.

    If the recorded guitar and the amplifier models are on the computer,
    they play (`guitar.py`). If not, the string model plays.
    """
    canvas = Canvas(seconds)
    by_tone: dict[str, list[Event]] = {}
    for event in events:
        tone = event.note.get("tone")
        by_tone.setdefault(tone if tone in AMPS else "clean", []).append(event)
    if guitar.available():
        for tone, group in by_tone.items():
            follow = fader(group, len(canvas.data), FADER_DB[tone])
            if tone in ("crunch", "high gain", "clean"):
                # Two performances with two different recordings of each note: far left
                # and right for the heavy tones, nearer for the clean tone.
                side_place = 0.92 if tone != "clean" else 0.6
                for side, seed in ((0, 11), (1, 23)):
                    dry = guitar_direct(_strokes(group, _take(seed)), seconds, side, seed)
                    wet = guitar.amplify(dry, tone)[: len(canvas.data)]
                    wet = wet * follow[: len(wet)]
                    if tone == "clean":
                        wet = _clean_level(wet)
                    canvas.add(0.0, effects.pan(wet, side_place * (2 * side - 1)))
            else:
                # The lead tone: one guitar in the centre, a wider vibrato on its long
                # notes, and soft echoes on the two sides.
                lead = [replace(stroke, vibrato=1.7 * stroke.vibrato) for stroke in _strokes(group)]
                dry = guitar_direct(lead, seconds, 0, 5)
                wet = effects.stereo(guitar.amplify(dry, tone)[: len(canvas.data)]) * 1.41
                canvas.add(0.0, wet)
                echoes = effects.delay(wet, LEAD_ECHO_SECONDS, 0.32, damping=0.6)
                canvas.add(0.0, echoes[: len(canvas.data)] * dsp.db(LEAD_ECHO_DB))
        return canvas.data
    for tone, group in by_tone.items():
        settings = AMPS[tone]
        if tone in ("crunch", "high gain", "clean"):
            # Two takes: far left and right for the heavy tones, nearer for the clean tone.
            side_place = 0.92 if tone != "clean" else 0.6
            for side, seed in ((-1.0, 11), (1.0, 23)):
                dry = amp.play(amp.GUITAR, _string_notes(group, seed=seed), seconds, seed=seed)
                wet = amp.amplify(dry, settings)[: len(canvas.data)]
                if tone == "clean":
                    # The distortion of the other tones is a compressor by itself.
                    wet = _clean_level(wet)
                canvas.add(0.0, effects.pan(wet, side_place * side))
        else:
            dry = amp.play(amp.GUITAR, _string_notes(group), seconds, seed=5)
            wet = amp.amplify(dry, settings)[: len(canvas.data)]
            canvas.add(0.0, effects.stereo(wet) * 1.41)
    return canvas.data


def _bass_samples(bank: banks.BassBank, events: list[Event], total: int) -> np.ndarray:
    """Return the direct signal of the bass guitar from the recorded notes (one channel)."""
    out = np.zeros(total)
    ordered = sorted(events, key=lambda event: event.start)
    for number, event in enumerate(ordered):
        note = event.note
        level, _end = accent_level(event)
        marks = note.articulations
        length = sounding(event)
        kind = "reg"
        if "stopped" in marks:
            kind = "ghost"  # a note with no pitch: the left hand stops the string
        elif "staccatissimo" in marks or ("staccato" in marks and event.seconds < 0.3):
            kind = "stac"
        # A recording starts 26 milliseconds before its note sounds (the finger is on the
        # string). The recording starts earlier by this time: the note is at its written
        # time. (To version 3.5 the notes of the bass were late by this time.)
        sample, gain, lead = bank.sample(kind, event.midi, level, number)
        body = sample[: int((lead + length + 0.05) * RATE)].astype(np.float64).copy()
        if len(body) < 64:
            continue
        if note.legato and kind == "reg":
            # A hammer-on or a slide: no stroke of the finger at the start. The note starts
            # inside the recording, a moment after the start of its sound.
            skip = int(0.03 * RATE)
            body = body[skip:]
            ramp = min(len(body), int(0.012 * RATE))
            body[:ramp] *= np.linspace(0.0, 1.0, ramp)
            gain *= 0.85
            lead = 0.0
        following = ordered[number + 1] if number + 1 < len(ordered) else None
        if note.glissando and following is not None and len(body) > 256:
            curve = np.zeros(len(body))
            begin = int(0.45 * len(body))
            curve[begin:] = np.linspace(0.0, following.midi - event.midi, len(body) - begin)
            body = dsp.bend(body.astype(np.float32), curve).astype(np.float64)
        if note.get("mute") == "palm":
            body = signal.sosfilt(dsp.lowpass(650.0, 2), body)
            body *= np.exp(-np.arange(len(body)) / (0.11 * RATE))
        fade = min(len(body), int(0.035 * RATE))
        body[-fade:] *= np.linspace(1.0, 0.0, fade)
        first = int(round((event.start - lead) * RATE))
        if first < 0:
            body, first = body[-first:], 0
        if first >= total:
            continue
        last = min(total, first + len(body))
        out[first:last] += body[: last - first] * gain
        if kind == "reg" and length > 0.18:
            noise, noise_gain, _lead = bank.sample("rel", event.midi, level, number)
            start = int(round((event.start + length) * RATE))
            stop = min(total, start + len(noise))
            if stop > start:
                out[start:stop] += noise[: stop - start] * noise_gain * 0.5
    return out


def render_bass(events: list[Event], seconds: float) -> np.ndarray:
    """Play the bass guitar: a clean low band and a band with grit, as in a studio mix.

    The notes come from the sample bank of a real bass. If the bank is not
    there, the string model plays. With the octave pedal on, a sine tone one
    octave lower follows each note.
    """
    canvas = Canvas(seconds)
    folder = banks.fetch_bass()
    if folder is not None:
        dry = _bass_samples(banks.BassBank(folder), events, len(canvas.data))
    else:
        dry = amp.play(amp.BASS, _string_notes(events), seconds, seed=3)[: len(canvas.data)]
    low = signal.sosfilt(np.vstack([dsp.lowpass(210.0, 4), dsp.highpass(28.0, 2)]), dry)
    grit = amp.amplify(signal.sosfilt(dsp.highpass(240.0, 2), dry), amp.BASS_GRIT)
    body = signal.sosfilt(np.vstack([dsp.highpass(180.0, 2), dsp.lowpass(2600.0, 2)]), dry)
    mixed = 1.25 * low + 0.45 * grit[: len(low)] + 0.7 * body
    canvas.add(0.0, effects.stereo(mixed) * 1.41)
    octave = [event for event in events if event.note.get("motor") == "on"]
    for number, event in enumerate(octave):
        level, level_end = accent_level(event)
        sound = synth.render_note(
            patches.BASS_SUB,
            event.midi - 12.0,
            sounding(event),
            0.85 * level,
            0.85 * level_end,
            seed=("octaver", number),
        )
        canvas.add(event.start, sound)
    return canvas.data


# ----------------------------------------------------------------------------
# Electric piano
# ----------------------------------------------------------------------------


def render_keys(events: list[Event], seconds: float, player: str = "keys") -> np.ndarray:
    """Play the electric piano from the sample bank of a Rhodes piano.

    The sound moves slowly between left and right, as in the amplifier of
    the instrument ("suitcase" model). A loud note has some distortion: the
    "bark" of the instrument. If the bank is not there, an FM patch plays.
    """
    folder = banks.fetch_rhodes()
    if folder is None:
        return render_substitute(events, seconds, player)
    bank = banks.RhodesBank(folder)
    total = int(seconds * RATE) + RATE
    out = np.zeros(total)
    for event in events:
        level, _end = accent_level(event)
        length = sounding(event)
        first = int(round(event.start * RATE))
        if first < 0 or first >= total:
            continue
        for sample, weight in bank.sample(event.midi, level):
            body = sample[: int((length + 0.2) * RATE)].astype(np.float64).copy()
            fade = min(len(body), int(0.16 * RATE))
            body[-fade:] *= np.linspace(1.0, 0.0, fade) ** 2
            last = min(total, first + len(body))
            out[first:last] += body[: last - first] * weight
    out = effects.saturate(out * 1.6, 5.0, bias=0.15) * 0.6
    time = np.arange(total) / RATE
    wave = 0.24 * np.sin(2 * np.pi * 4.7 * time)
    return np.stack([out * (1.0 + wave), out * (1.0 - wave)], axis=1).astype(np.float32)


# ----------------------------------------------------------------------------
# Players that MuseScore plays, with a synthesizer patch if MuseScore is not there
# ----------------------------------------------------------------------------

SUBSTITUTES = {
    "tenor saxophone": "lead wind", "alto saxophone": "lead wind",
    "baritone saxophone": "lead wind",
    "trumpet in B-flat": "synth brass", "tenor trombone": "synth brass",
    "violin": "pad warm", "viola": "pad warm", "violoncello": "pad warm",
    "electric piano": "epiano fm", "wurlitzer": "epiano fm", "organ": "pad warm",
}  # fmt: skip


def render_substitute(events: list[Event], seconds: float, player: str) -> np.ndarray:
    """Play a part of a real instrument with a synthesizer patch."""
    canvas = Canvas(seconds)
    by_patch: dict[str, list[Event]] = {}
    for event in events:
        by_patch.setdefault(SUBSTITUTES[event.note.instrument], []).append(event)
    for name, group in by_patch.items():
        if name in patches.FM:
            for number, event in enumerate(group):
                level, _end = accent_level(event)
                sound = synth.render_fm(patches.FM[name], event.midi, sounding(event), level,
                                        seed=(player, number))  # fmt: skip
                canvas.add(event.start, sound)
        else:
            patch = patches.SUBTRACTIVE[name]
            if patch.glide > 0:
                _lines(canvas, patch, group, player)
            else:
                for number, event in enumerate(group):
                    level, level_end = accent_level(event)
                    sound = synth.render_note(patch, event.midi, sounding(event), level, level_end,
                                              seed=(player, number))  # fmt: skip
                    canvas.add(event.start, sound)
    return canvas.data
