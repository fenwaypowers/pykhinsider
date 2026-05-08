import argparse
import re
import sys
from urllib.parse import urlparse

from pykhinsider.models import Album, Track


def normalize_url(url: str) -> tuple[str, str]:
    """
    Normalize a user-supplied URL.

    Returns:
        (normalized_url, type)

    Types:
        - album
        - track
    """

    parsed = urlparse(url)

    # Direct download link
    if "vgmtreasurechest.com" in parsed.netloc:
        parts = parsed.path.split("/")

        # Remove random 8-char directory
        # /soundtracks/<album>/<random>/<file>
        if len(parts) >= 5:
            album = parts[2]
            filename = parts[4]

            track_url = (
                "https://downloads.khinsider.com"
                f"/game-soundtracks/album/{album}/{filename}"
            )

            return track_url, "track"

    # KHInsider track page
    if url.endswith(".mp3"):
        return url, "track"

    # KHInsider album page
    return url, "album"


def main():
    parser = argparse.ArgumentParser(
        prog="pykhinsider",
        description="Download music from KHInsider.",
    )

    parser.add_argument(
        "url",
        help="KHInsider album/song URL or direct download link",
    )

    parser.add_argument(
        "-f",
        "--format",
        choices=["mp3", "flac"],
        default="mp3",
        help="audio format to download",
    )

    parser.add_argument(
        "-o",
        "--output",
        default=".",
        help="output directory",
    )

    parser.add_argument(
        "--dump-links",
        "--print-links",
        action="store_true",
        dest="dump_links",
        help="print direct download links only",
    )

    args = parser.parse_args()

    try:
        url, url_type = normalize_url(args.url)

        # Album
        if url_type == "album":
            album = Album(url)

            if args.dump_links:
                album.print_all_ddl(format=args.format)
            else:
                album.download_all(
                    format=args.format,
                    dest=args.output,
                )

        # Track
        elif url_type == "track":
            track = Track(url)

            if args.dump_links:
                track.print_ddl(format=args.format)
            else:
                track.download(
                    format=args.format,
                    dest=args.output,
                )

    except KeyboardInterrupt:
        sys.exit(130)

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
