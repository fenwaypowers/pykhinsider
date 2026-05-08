from http.client import REQUEST_TIMEOUT

from bs4 import BeautifulSoup
import requests

from pykhinsider.constants import HEADERS
from pykhinsider.exceptions import InvalidURLError


def get_soup(url: str) -> BeautifulSoup:
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

    except requests.RequestException as e:
        raise InvalidURLError(
            f"Failed to fetch: {url}"
        ) from e

    return BeautifulSoup(response.text, "html.parser")