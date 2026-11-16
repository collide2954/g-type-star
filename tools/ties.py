"""Find ties that go to a note with a different pitch (a tie must hold one pitch)."""

from __future__ import annotations

from gtypestar.notation import music
from gtypestar.work import build


def notes(elements, found):
    for element in elements:
        if isinstance(element, music.Note | music.Rest):
            found.append(element)
        elif isinstance(element, music.Group):
            if element.kind == "parallel":
                continue
            notes(element.children, found)
    return found


def main() -> None:
    work = build()
    for player in work.orchestra.players:
        for first_bar, chunk in work.chunks[player.id]:
            sequence = notes(chunk.children, [])
            for index, note in enumerate(sequence):
                if not isinstance(note, music.Note):
                    continue
                if not any(post.kind == "tie" for post in note.posts):
                    continue
                following = sequence[index + 1] if index + 1 < len(sequence) else None
                own = sorted(p.pitch.midi for p in note.pitches)
                if following is None:
                    continue
                if isinstance(following, music.Rest):
                    print(f"{player.id}: section at bar {first_bar}: a tie goes to a rest")
                    continue
                other = sorted(p.pitch.midi for p in following.pitches)
                if not set(own) & set(other):
                    names = " ".join(p.pitch.name for p in note.pitches)
                    later = " ".join(p.pitch.name for p in following.pitches)
                    print(f"{player.id}: section at bar {first_bar}: tie from {names} to {later}")


if __name__ == "__main__":
    main()
