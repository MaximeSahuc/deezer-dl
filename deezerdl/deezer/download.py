import os

from deezer.deezer import config, test_deezer_login, get_song_infos_from_deezer_website, download_song, get_deezer_favorites, parse_deezer_playlist, parse_deezer_track, parse_deezer_user_playlists, TYPE_TRACK
from deezer.utils import format_song_filename

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

    playlist_dir = os.path.join(config['deezer']['music_dir'], 'Playlists', playlist_name.replace(' ', '_'))
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


def download_track(track):
    playlist_dir = os.path.join(config['deezer']['music_dir'], 'Tracks')
    os.makedirs(playlist_dir, exist_ok=True)

    data = parse_deezer_track(track)

    SNG_TITLE = data['SNG_TITLE']
    ART_NAME = data['ART_NAME']

    try:
        song_filename = format_song_filename(ART_NAME, SNG_TITLE)
        song_path = os.path.join(playlist_dir, song_filename)
        
        # We only support FLAC and MP3
        if os.path.exists(song_path+'.flac') or os.path.exists(song_path+'.mp3'):
            return

        download_song(data, song_path)
    except Exception as e:
        print(e)
        return 1


def download_all_playlists():
    user = config['deezer']['user_id']
    result = parse_deezer_user_playlists(user)
    playlists = result['data']

    print(f"Loaded {len(playlists)}/{result['total']} playlists")

    for playlist in playlists:
        pl_title = playlist['TITLE']
        pl_nb_song = playlist['NB_SONG']
        pl_id = playlist['PLAYLIST_ID']

        print(f"  Downloading {pl_title} : {pl_nb_song} tracks")

        download_playlist(pl_id)
        print(f"  Downloaded {pl_title}")