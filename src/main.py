#!/usr/bin/env python3

import os
import sys

from deezer.config import ConfigManager
from deezer.client import DeezerClient


CONFIG_FILE_PATH = os.path.join(os.path.expanduser("~"), ".deezer-dl", "config.yml")


def check_requirements():
    # Check if on Linux or MacOS
    platform = sys.platform
    if not platform.startswith("linux") and not platform.startswith("darwin"):
        print("OS not supported yet! Supports only Linux or MacOS (darwin)")
        exit(1)


def print_help():
    print("""Usage: deezer-dl <argument>

Download Music from Deezer

arguments:
  url <url>                              URL of a Deezer track, album or playlist 
  favorites                              Download favorites tracks from user in config file
  all                                    Download all favorite tracks, albums and playlists of the configured user
  all-playlists                          Download all playlists of the configured user
  all-albums                             Download all albums of the configured user
  all-from-artist <artist id or url>     Download all songs and albums from given artist
  all-from-favorite-artists [user id]    Download all songs and albums from favorite artists of the specified user or configured user
  export-all-user-data [user id]         Export all user data as json files: favorite tracks, playlists, saved albums, favorite artists""")


def main():
    # Check system requirements
    check_requirements()

    # Print help message if no arguments provided
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print_help()
        exit(1)

    # Subcommand
    subcommand = sys.argv[1]

    # Load config
    cm = ConfigManager(CONFIG_FILE_PATH)

    # Init Deezer session
    dc = DeezerClient(config_manager=cm)

    # Subcommand
    match subcommand:
        case "favorites":
            print("Downloading all favorite tracks of the configured user.")
            dc.get_downloader().download_favorites()

        case "all-playlists":
            print("Downloading all playlists of the configured user.")
            dc.get_downloader().download_all_playlists()

        case "all-albums":
            print("Downloading all albums of the configured user.")
            dc.get_downloader().download_all_albums()

        case "all-from-artist":
            if len(sys.argv) != 3:
                print("Please provide an artist ID or URL")
                exit(1)

            artist_id = sys.argv[2]

            print(f"Downloading all songs from artist : {artist_id}")
            dc.get_downloader().download_all_from_artist(artist_id)

        case "all-from-favorite-artists":
            user_id = None

            if len(sys.argv) == 3:
                user_id = sys.argv[2]

            dc.get_downloader().download_all_from_favorite_artists(user_id)

        case "all":
            print("Download all favorite tracks, albums and playlists")
            dc.get_downloader().download_all()

        case "url":
            if len(sys.argv) != 3:
                print("Please provide an URL")
                exit(1)

            url = sys.argv[2]

            dc.get_downloader().download_from_url(url)

        case "export-all-user-data":
            user_id = None
            if len(sys.argv) == 3:
                user_id = sys.argv[2]

            dc.export_all_user_data(user_id)

        case _:
            print("Error: invalid sub-command")
            exit(1)


if __name__ == "__main__":
    main()
