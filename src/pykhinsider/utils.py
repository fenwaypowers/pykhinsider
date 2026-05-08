import requests

from bs4 import BeautifulSoup

from pykhinsider.constants import (
    HEADERS,
    REQUEST_TIMEOUT,
)

session = requests.Session()
session.headers.update(HEADERS)


def get(url: str, **kwargs):
    return session.get(
        url,
        timeout=REQUEST_TIMEOUT,
        **kwargs,
    )


def get_soup(url: str) -> BeautifulSoup:
    response = get(url)

    response.raise_for_status()

    return BeautifulSoup(response.text, "html.parser")
