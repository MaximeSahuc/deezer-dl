#!/usr/bin/env python3

import sys
import os
import argparse
import json

from deezer.deezer import config, test_deezer_login, get_song_infos_from_deezer_website, download_song, get_deezer_favorites, parse_deezer_playlist, TYPE_TRACK
from deezer.utils import format_song_filename

if not sys.platform.startswith('linux'):
    print('Only linux is supported.')
    sys.exit(1)


def print_help():
    print("Commands:\n check\n deezerdl https://deezer.com/...")


def download_favorites():
    favorite_playlist = get_deezer_favorites(config['deezer']['user_id'])
    playlist_path = config['deezer']['music_dir'] + '/Likes'
    print(playlist_path)
    
    os.makedirs(playlist_path, exist_ok=True)

    for song_id in favorite_playlist:
        try:
            song_info = get_song_infos_from_deezer_website(TYPE_TRACK, song_id)
            song_filename = format_song_filename(song_info['ART_NAME'],song_info['SNG_TITLE'])
            song_path = os.path.join(playlist_path, song_filename)
            # We only support FLAC and MP3
            if os.path.exists(song_path+'.flac') or os.path.exists(song_path+'.mp3'):
                continue
            download_song(song_info, song_path)            
        except Exception as e:
            print(e)
            pass


def download_playlist(playlist):
    playlist_name, tracks = parse_deezer_playlist(playlist)

    playlist_dir = config['deezer']['music_dir'] + playlist_name.replace(' ', '_')
    os.makedirs(playlist_dir, exist_ok=True)

    for track in tracks:
        SNG_TITLE = track['SNG_TITLE']
        ART_NAME = track['ART_NAME']

        try:
            song_filename = format_song_filename(ART_NAME, SNG_TITLE)
            song_path = os.path.join(playlist_dir, song_filename)
            
            # We only support FLAC and MP3
            if os.path.exists(song_path+'.flac') or os.path.exists(song_path+'.mp3'):
                continue

            download_song(track, song_path)            
        except Exception as e:
            print(e)
            pass


def main():
    description = """
    check      Verify Deezer login.
    download   Download favorites.    
    """
    
    if len(sys.argv) != 2:
        print_help()
    else:
        arg = sys.argv[1]
        
        if arg == 'check':
            test_deezer_login()
        
        elif arg == 'favorites':
            download_favorites()
        
        else:
            # Assume its a playlist link
            # TODO : check if its a track
            download_playlist(arg)


if __name__ == "__main__":
    main()