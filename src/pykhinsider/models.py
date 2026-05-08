from dataclasses import dataclass, field
from typing import Optional


@dataclass(slots=True)
class Track:
    page_url: str
    mp3_url: str | None = None
    flac_url: str | None = None


@dataclass(slots=True)
class Album:
    url: str

    tracks: list[Track] = field(default_factory=list)

    @property
    def track_count(self) -> int:
        return len(self.tracks)
