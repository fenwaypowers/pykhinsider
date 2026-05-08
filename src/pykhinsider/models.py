from dataclasses import dataclass, field
from typing import Optional


from bs4 import BeautifulSoup
import requests

from pykhinsider.constants import (
    HEADERS,
    REQUEST_TIMEOUT,
)
from pykhinsider.exceptions import ParseError


class Track:
    def __init__(self, page_url: str):
        self.page_url = page_url

        self.mp3_url: str | None = None
        self.flac_url: str | None = None

        self._resolved = False

    @property
    def resolved(self) -> bool:
        return self._resolved

    def resolve(self) -> None:
        """
        Resolve downloadable audio links from the track page.
        """

        if self._resolved:
            return

        response = requests.get(
            self.page_url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for link in soup.find_all("a", href=True):
            href = link["href"]

            if href.endswith(".mp3"):
                self.mp3_url = href

            elif href.endswith(".flac"):
                self.flac_url = href

        if self.mp3_url is None and self.flac_url is None:
            raise ParseError(
                f"No downloadable links found: {self.page_url}"
            )

        self._resolved = True

@dataclass(slots=True)
class Album:
    url: str

    tracks: list[Track] = field(default_factory=list)

    @property
    def track_count(self) -> int:
        return len(self.tracks)
