from bs4 import BeautifulSoup
import requests
from pykhinsider.models import Album, Track
from pykhinsider.constants import HEADERS


def parse_album(url: str) -> Album:
    response = requests.get(url, headers = HEADERS)
    
    track_list = []

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        all_tr = soup.find_all("tr")

        for tr in all_tr:
            if "play track" in str(tr.get_text):
                cells = tr.find_all("td")

                # Extract the relevant data from the cells
                title_cell = cells[3].find("a")
                track_url = title_cell["href"]
                track_list.append(parse_track(track_url))
    
    return Album(url=url, tracks=track_list)


def parse_track(url: str) -> Track:
    response = requests.get(url)

    flac_url = None
    mp3_url = None

    if response.status_code == 200:
            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")

            for p in soup.find_all("p"):
                if "FLAC" in str(p.find("a").find("span").get_text):
                        flac_url = str(p.find("a").get_text).split('href="')[1].split('">')[0]
                elif "MP3" in str(p.find("a").find("span").get_text):
                        mp3_url = str(p.find("a").get_text).split('href="')[1].split('">')[0]

    return Track(
        page_url=url,mp3_url=mp3_url,flac_url=flac_url
    )
