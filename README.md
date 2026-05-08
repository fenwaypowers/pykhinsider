# pykhinsider

Command line tool to download entire albums or individual songs from [KHinsider](https://downloads.khinsider.com) in both MP3 and FLAC format.

It also works as a python package and you can use it directly in your own scripts.

## Features
- Download any MP3 or FLAC track from KHinsider
- Download any album from KHinsider
- Dump direct download links to stdout

## How To Install

### Windows:
- Simply download the most recent `.exe` file from the [Releases tab](https://github.com/fenwaypowers/pykhinsider/releases).

### Linux
- Simply download the most recent binary from the [Releases tab](https://github.com/fenwaypowers/pykhinsider/releases).

## Command-Line Use

```
usage: pykhinsider [-h] [-f {mp3,flac}] [-o OUTPUT] [--dump-links] url

Download music from KHInsider.

positional arguments:
  url                   KHInsider album/song URL or direct download link

options:
  -h, --help            show this help message and exit
  -f {mp3,flac}, --format {mp3,flac}
                        audio format to download
  -o OUTPUT, --output OUTPUT
                        output directory
  --dump-links, --print-links
                        print direct download links only
```

## Install as a package

Make sure you have Python 3.10 or later installed.

Clone the repository and install locally:

```bash
git clone https://github.com/fenwaypowers/pykhinsider
cd pykhinsider
pip install -e .
```

Example Python use:

```py
from pykhinsider import Album, Track

# download track
track = Track(
    "https://downloads.khinsider.com/game-soundtracks/album/wii-music-collection/03.%2520Mii%2520Channel.mp3"
)

track.download(format="flac", dest=".")

# download album
album = Album(
    "https://downloads.khinsider.com/game-soundtracks/album/wii-music-collection/"
)

album.download_all(format="mp3", dest=".")

# print direct download links
track.resolve() # retrieves direct download links

print(track.mp3_url)
print(track.flac_url)
```

## License

[MIT](https://github.com/fenwaypowers/pykhinsider/blob/main/LICENSE)

## Reporting Issues

When reporting bugs, please include:

- the command/code you ran
- the expected behavior
- the actual behavior
- the full error message
