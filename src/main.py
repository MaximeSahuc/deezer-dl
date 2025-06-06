#!/usr/bin/env python3

import os
import sys

from deezer.config import ConfigManager
from deezer.client import DeezerClient


CONFIG_FILE_PATH = os.path.join(
    os.path.expanduser("~"), ".config", "deezer-dl", "config.yml"
)


def check_requirements():
    # Check if on Linux or MacOS
    platform = sys.platform
    if not platform.startswith("linux") and not platform.startswith("darwin"):
        print("OS not supported yet! Supports only Linux or MacOS (darwin)")
        exit(1)


def print_help():
    print("""Usage: deezer-dl url [check] [favorites]

Download Music from Deezer

arguments:
  url <url>      URL of a Deezer track, album or playlist 
  favorites      Download favorites tracks from user in config file
  all-playlists  Download all playlists of the configured user
  all-albums     Download all albums of the configured user""")


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

        case "all":
            print("Download all favorite tracks, albums and playlist")
            user_id = None
            if len(sys.argv) == 3:
                user_id = sys.argv[2]

            dc.get_downloader().download_all()
        case "url":
            if len(sys.argv) != 3:
                print("Please provide an URL")

            url = sys.argv[2]

            dc.get_downloader().download_from_url(url)

        case _:
            print("Error: invalid sub-command")
            exit(1)


if __name__ == "__main__":
    main()
