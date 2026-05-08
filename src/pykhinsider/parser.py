from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests import RequestException

from pykhinsider.constants import BASE_URL, HEADERS, REQUEST_TIMEOUT
from pykhinsider.exceptions import InvalidURLError, ParseError
from pykhinsider.models import Album, Track


def parse_album(url: str) -> Album:
    """
    Parse a KHInsider album page into an Album object.
    """

    soup = get_soup(url)

    tracks: list[Track] = []

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

            tracks.append(Track(page_url=track_url))

        except Exception:
            # Skip malformed rows instead of crashing entire parse
            continue

    if not tracks:
        raise ParseError(
            f"No tracks found on album page: {url}"
        )

    return Album(
        url=url,
        tracks=tracks,
    )

def get_soup(url: str) -> BeautifulSoup:
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

    except RequestException as e:
        raise InvalidURLError(
            f"Failed to fetch: {url}"
        ) from e

    return BeautifulSoup(response.text, "html.parser")
