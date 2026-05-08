import os
from urllib.parse import urljoin
import requests
import sys
import time

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

        soup = get_soup(self.page_url)

        for link in soup.find_all("a", href=True):
            href = link["href"]

            if href.endswith(".mp3"):
                self.mp3_url = href

            elif href.endswith(".flac"):
                self.flac_url = href

        if self.mp3_url is None and self.flac_url is None:
            raise ParseError(f"No downloadable links found: {self.page_url}")

        self._resolved = True

    def download(
        self,
        format: str = "mp3",
        dest: str = ".",
        print_progress: bool = False,
    ) -> str:
        """
        Download the track and return the saved filepath.
        """

        if not self._resolved:
            self.resolve()

        url = self.mp3_url if format == "mp3" else self.flac_url

        if url is None:
            raise ParseError(
                f"{format.upper()} link not found for track: {self.page_url}"
            )

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            stream=True,
        )

        response.raise_for_status()

        filename = url.split("/")[-1]
        filepath = os.path.join(dest, filename)

        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0

        start_time = time.time()

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if not chunk:
                    continue

                f.write(chunk)

                if print_progress:
                    downloaded += len(chunk)

                    elapsed = max(time.time() - start_time, 0.001)

                    speed = downloaded / elapsed  # bytes/sec

                    percent = (downloaded / total_size) * 100 if total_size > 0 else 0

                    downloaded_mb = downloaded / (1024 * 1024)
                    total_mb = total_size / (1024 * 1024)
                    speed_mb = speed / (1024 * 1024)

                    sys.stdout.write(
                        (
                            f"\r{filename} | "
                            f"{percent:6.2f}% | "
                            f"{downloaded_mb:7.2f}/{total_mb:.2f} MB | "
                            f"{speed_mb:.2f} MB/s"
                        )
                    )

                    sys.stdout.flush()

        if print_progress:
            print()

        return filepath

    def print_ddl(self, format: str = "mp3") -> None:
        if not self._resolved:
            self.resolve()

        url = self.mp3_url if format == "mp3" else self.flac_url

        if url is not None:
            print(url)


class Album:
    def __init__(self, url: str):
        self.url: str = url
        self.title = url.split("/")[-1]
        self.tracks: list[Track] = []

        self._populated = False

    @property
    def track_count(self) -> int:
        return len(self.tracks)

    def populate_tracks(self) -> None:
        if self._populated:
            return

        soup = get_soup(self.url)

        for row in soup.find_all("tr"):
            try:
                if row.find("div", class_="playTrack") is None:
                    continue

                title_cell = row.find("td", class_="clickable-row")

                if title_cell is None:
                    continue

                link = title_cell.find("a")

                if link is None:
                    continue

                track_url = link.get("href")

                if not track_url:
                    continue

                track_url = urljoin(BASE_URL, track_url)

                self.tracks.append(Track(page_url=track_url))

            except Exception:
                continue

        if not self.tracks:
            raise ParseError(f"No tracks found on album page: {self.url}")

        self._populated = True

    def download_all(
        self, format: str = "mp3", dest: str = ".", print_progress: bool = False
    ) -> None:
        """
        Download all tracks in the album to the specified destination.
        """

        if not self.title:
            self.title = "Unknown Album"

        dest = os.path.join(dest, self.title)
        os.makedirs(dest, exist_ok=True)

        if not self._populated:
            self.populate_tracks()

        for track in self.tracks:
            try:
                track.download(format=format, dest=dest, print_progress=print_progress)
            except Exception as e:
                print(f"Failed to download track: {track.page_url}")
                print(e)

    def print_all_ddl(self, format: str = "mp3") -> None:
        if not self._populated:
            self.populate_tracks()

        for track in self.tracks:
            track.print_ddl(format=format)
