from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests

from pykhinsider.constants import (
    BASE_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from pykhinsider.exceptions import ParseError
from pykhinsider.utils import get_soup


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


    def download(self, format: str = "mp3") -> bytes:
        """
        Download the track in the specified format (mp3 or flac).
        """

        if not self._resolved:
            self.resolve()

        url = None

        if format == "mp3":
            url = self.mp3_url
        elif format == "flac":
            url = self.flac_url
        else:
            raise ValueError(f"Unsupported format: {format}")

        if url is None:
            raise ParseError(
                f"{format.upper()} link not found for track: {self.page_url}"
            )

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        return response.content


class Album:
    def __init__(self, url: str):
        self.url: str= url
        self.tracks: list[Track] = []
        self.populate_tracks()
    

    @property
    def track_count(self) -> int:
        return len(self.tracks)
    

    def populate_tracks(self) -> None:
        soup = get_soup(self.url)

        for row in soup.find_all("tr"):
            try:
                if "play track" not in row.get_text().lower():
                    continue

                cells = row.find_all("td")

                if len(cells) < 4:
                    continue

                title_cell = cells[3].find("a")

                if title_cell is None:
                    continue

                track_url = title_cell.get("href")

                if not track_url:
                    continue

                track_url = urljoin(BASE_URL, track_url)

                self.tracks.append(Track(page_url=track_url))

            except Exception:
                # Skip malformed rows instead of crashing entire parse
                continue

        if not self.tracks:
            raise ParseError(
                f"No tracks found on album page: {self.url}"
            )
        
    
    def download_all(self, format: str = "mp3") -> list[bytes]:
        """
        Download all tracks in the album in the specified format (mp3 or flac).
        Returns a list of binary content for each downloaded track.
        """

        downloaded_tracks = []

        for track in self.tracks:
            try:
                content = track.download(format=format)
                downloaded_tracks.append(content)
            except Exception:
                # Skip tracks that fail to download instead of crashing entire album download
                continue

        return downloaded_tracks
