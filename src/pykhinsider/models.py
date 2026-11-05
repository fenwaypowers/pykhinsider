import os
from urllib.parse import urljoin
from urllib.parse import unquote
import requests
import sys
import time
from typing import Callable

from pykhinsider.constants import (
    BASE_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from pykhinsider.exceptions import ParseError
from pykhinsider.utils import get_soup


def sanitize_filename(name: str) -> str:
    invalid = '<>:"/\\|?*'
    sanitized = "".join("_" if char in invalid else char for char in name)
    return sanitized.strip().rstrip(".")


def _with_position(
    callback: Callable[[str], None], index: int, total: int
) -> Callable[[str], None]:
    """Wrap callback so each message is suffixed with "| index/total"."""

    def wrapped(msg: str) -> None:
        callback(f"{msg} | {index}/{total}")

    return wrapped


class Track:
    def __init__(self, page_url: str, flaresolverr_url: str | None = None):
        self.page_url = page_url
        self.flaresolverr_url = flaresolverr_url

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

        soup = get_soup(self.page_url, flaresolverr_url=self.flaresolverr_url)

        for link in soup.find_all("a", href=True):
            href = link.get("href")

            if not isinstance(href, str):
                continue

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
        progress_callback: Callable[[str], None] | None = None,
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

        filename = unquote(url.split("/")[-1])
        filename = sanitize_filename(filename)
        filepath = os.path.join(dest, filename)

        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0

        start_time = time.time()

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if not chunk:
                    continue

                f.write(chunk)

                if print_progress or progress_callback:
                    downloaded += len(chunk)

                    elapsed = max(time.time() - start_time, 0.001)

                    speed = downloaded / elapsed  # bytes/sec

                    percent = (downloaded / total_size) * 100 if total_size > 0 else 0

                    downloaded_mb = downloaded / (1024 * 1024)
                    total_mb = total_size / (1024 * 1024)
                    speed_mb = speed / (1024 * 1024)

                    message = (
                        f"{filename} | "
                        f"{percent:6.2f}% | "
                        f"{downloaded_mb:7.2f}/{total_mb:.2f} MB | "
                        f"{speed_mb:.2f} MB/s"
                    )

                    if progress_callback:
                        progress_callback(message)

                    if print_progress:
                        sys.stdout.write(f"\r{message}")
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
    def __init__(self, url: str, flaresolverr_url: str | None = None):
        self.url: str = url
        self.title = url.split("/")[-1]
        self.tracks: list[Track] = []

        self._populated = False
        self.flaresolverr_url = flaresolverr_url

    @property
    def track_count(self) -> int:
        return len(self.tracks)

    def populate_tracks(self) -> None:
        if self._populated:
            return

        soup = get_soup(self.url, flaresolverr_url=self.flaresolverr_url)

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

                if not isinstance(track_url, str) or not track_url:
                    continue

                track_url = urljoin(BASE_URL, track_url)

                self.tracks.append(
                    Track(page_url=track_url, flaresolverr_url=self.flaresolverr_url)
                )

            except Exception:
                continue

        if not self.tracks:
            raise ParseError(f"No tracks found on album page: {self.url}")

        self._populated = True

    def download_all(
        self,
        format: str = "mp3",
        dest: str = ".",
        print_progress: bool = False,
        flaresolverr_url: str | None = None,
        progress_callback: Callable[[str], None] | None = None,
    ) -> None:
        """
        Download all tracks in the album to the specified destination.

        If given, progress_callback receives each track's progress message
        suffixed with the track's position in the album (e.g. "| 3/12").
        """

        if flaresolverr_url:
            self.flaresolverr_url = flaresolverr_url

        if not self.title:
            self.title = "Unknown Album"

        dest = os.path.join(dest, self.title)
        os.makedirs(dest, exist_ok=True)

        if not self._populated:
            self.populate_tracks()

        total = len(self.tracks)

        for index, track in enumerate(self.tracks, start=1):
            track_callback = (
                _with_position(progress_callback, index, total)
                if progress_callback
                else None
            )

            try:
                track.flaresolverr_url = self.flaresolverr_url
                track.download(
                    format=format,
                    dest=dest,
                    print_progress=print_progress,
                    progress_callback=track_callback,
                )
            except Exception as e:
                print(f"Failed to download track: {track.page_url}")
                print(e)

    def print_all_ddl(self, format: str = "mp3") -> None:
        if not self._populated:
            self.populate_tracks()

        for track in self.tracks:
            track.print_ddl(format=format)
