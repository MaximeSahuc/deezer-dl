#!/usr/bin/env python3

import sys

from deezer.download import download_favorites, download_playlist, download_track, download_all_playlists

# Check if on Linux
if not sys.platform.startswith('linux'):
    print('Only linux is supported.')
    sys.exit(1)


def print_help():
    print("""Usage: deezer-dl url [check] [favorites]

Download Music from Deezer

arguments:
  url          URL of a Deezer track or playlist 
  check        Test Deezer Token
  favorites    Download favorites tracks from user in config file""")


def main() -> int:
    if len(sys.argv) != 2:
        print_help()
        return 1
    else:
        arg = sys.argv[1]

        if arg == 'check':
            test_deezer_login()

        elif arg == 'favorites':
            download_favorites()

        elif arg == 'all':
            print("download all user's playlists")
            download_all_playlists()

        else:
            if 'track' in arg:
                download_track(arg)
            elif 'playlist' in arg:
                download_playlist(arg)
            else:
                print('Cannot detect link type')
                return 1
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())