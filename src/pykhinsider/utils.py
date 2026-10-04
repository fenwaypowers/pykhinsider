import requests

from bs4 import BeautifulSoup

from pykhinsider.constants import HEADERS, REQUEST_TIMEOUT

session = requests.Session()
session.headers.update(HEADERS)


def _persist_cookies(response: requests.Response) -> None:
    session.cookies.update(response.cookies)


def get_flaresolverr(flaresolverr_url: str, url: str) -> requests.Response:
    endpoint = flaresolverr_url.rstrip("/")

    if not endpoint.endswith("/v1"):
        endpoint += "/v1"

    data = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": 60000,
    }

    response = requests.post(
        endpoint,
        json=data,
        timeout=65,
    )

    try:
        js = response.json()
    except requests.JSONDecodeError as e:
        raise RuntimeError(
            f"FlareSolverr returned invalid JSON ({response.status_code})"
        ) from e

    if js.get("status") != "ok" or "solution" not in js:
        raise RuntimeError(f"FlareSolverr failed: {js.get('message', 'Unknown error')}")

    solution = js["solution"]

    mock = requests.Response()
    mock.status_code = solution["status"]
    mock._content = solution["response"].encode("utf-8")
    mock.url = solution["url"]
    mock.headers.update(solution.get("headers", {}))

    for cookie in solution.get("cookies", []):
        mock.cookies.set(cookie["name"], cookie["value"])

    return mock


def get(url: str, **kwargs):
    return session.get(
        url,
        timeout=REQUEST_TIMEOUT,
        **kwargs,
    )


def get_soup(url: str, flaresolverr_url: str = None) -> BeautifulSoup:
    response = get(url)
    if response.status_code == 403 and flaresolverr_url:
        print(
            f"Got 403 Access forbidden error, trying FlareSolverr at {flaresolverr_url}"
        )
        response = get_flaresolverr(flaresolverr_url, url)
        _persist_cookies(response)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")
