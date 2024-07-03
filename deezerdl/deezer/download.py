import os

from termcolor import colored
from alive_progress import alive_bar

from deezer.deezer import config, test_deezer_login, get_song_infos_from_deezer_website, download_song, get_deezer_favorites, parse_deezer_playlist, parse_deezer_track, parse_deezer_user_playlists, TYPE_TRACK
from deezer.utils import format_song_filename

def create_song_link(source, dest):
    """
    Create a hard link
    """
    os.link(source, dest)


def download_favorites():
    favorite_playlist = get_deezer_favorites(config['deezer']['user_id'])
    playlist_dir = config['deezer']['music_dir'] + '/Likes'
    
    # Create playlist directory
    os.makedirs(playlist_dir, exist_ok=True)

    # Download playlist
    progress_bar_title = colored('Favorites', 'red')
    with alive_bar(len(favorite_playlist), bar='classic2', spinner='waves2', length=50, stats=False, elapsed=False, dual_line=True, title=progress_bar_title) as progress_bar:
        for song_id in favorite_playlist:
            track = get_song_infos_from_deezer_website(TYPE_TRACK, song_id)
            
            song_title = track['SNG_TITLE']
            artist_name = track['ART_NAME']
            song_filename = format_song_filename(artist_name, song_title)

            progress_bar.text(' - ' + colored(song_filename, 'blue'))

            # Download track
            if config["deezer"]["use_hard_links"]:
                song_download_path = os.path.join(config['deezer']['music_dir'], 'Tracks', song_filename + '.mp3') # Download song to 'Tracks' folder
                song_final_path = os.path.join(playlist_dir, song_filename + '.mp3')

                # Skip if file already exits in final playlist folder
                if os.path.exists(song_final_path):
                    progress_bar() # increment progress bar
                    continue
                elif os.path.exists(song_download_path):
                    # Track exists in 'Tracks' folder, creating hard link to final playlist folder
                    create_song_link(song_download_path, song_final_path)
                else:
                    # Track not found, downloading it to 'Tracks' folder and creating hard link to final playlist folder
                    try:
                        download_song(track, song_download_path)
                        create_song_link(song_download_path, song_final_path)
                    except Exception as e:
                        pass
                    
            else:
                song_path = os.path.join(playlist_dir, song_filename + '.mp3')

                # Skip download if file already exits
                if os.path.exists(song_path):
                    progress_bar() # increment progress bar
                    continue
            
                try:
                    download_song(track, song_path)
                except Exception as e:
                    print(e)
                    pass

            progress_bar() # increment progress bar


def download_playlist(playlist):
    playlist_name, tracks = parse_deezer_playlist(playlist)
    playlist_dir = os.path.join(config['deezer']['music_dir'], 'Playlists', playlist_name.replace(' ', '_'))
    
    # Create playlist directory
    os.makedirs(playlist_dir, exist_ok=True)

    # Download playlist
    progress_bar_title = colored(playlist_name, 'red')
    with alive_bar(len(tracks), bar='classic2', spinner='waves2', length=50, stats=False, elapsed=False, dual_line=True, title=progress_bar_title) as progress_bar:
        for track in tracks:
            song_title = track['SNG_TITLE']
            artist_name = track['ART_NAME']
            
            progress_bar.text(' - ' + colored(song_filename, 'blue'))

            song_filename = format_song_filename(artist_name, song_title)

            # Download track
            if config["deezer"]["use_hard_links"]:
                song_download_path = os.path.join(config['deezer']['music_dir'], 'Tracks', song_filename + '.mp3') # Download song to 'Tracks' folder
                song_final_path = os.path.join(playlist_dir, song_filename + '.mp3')

                # Skip if file already exits in final playlist folder
                if os.path.exists(song_final_path):
                    progress_bar() # increment progress bar
                    continue
                elif os.path.exists(song_download_path):
                    # Track exists in 'Tracks' folder, creating hard link to final playlist folder
                    create_song_link(song_download_path, song_final_path)
                else:
                    # Track not found, downloading it to 'Tracks' folder and creating hard link to final playlist folder
                    try:
                        download_song(track, song_download_path)
                        create_song_link(song_download_path, song_final_path)
                    except Exception as e:
                        pass
                    
            else:
                song_path = os.path.join(playlist_dir, song_filename + '.mp3')

                # Skip download if file already exits
                if os.path.exists(song_path):
                    progress_bar() # increment progress bar
                    continue
            
                try:
                    download_song(track, song_path)
                except Exception as e:
                    print(e)
                    pass

            progress_bar() # increment progress bar


def download_track(track):
    playlist_dir = os.path.join(config['deezer']['music_dir'], 'Tracks')
    os.makedirs(playlist_dir, exist_ok=True)

    data = parse_deezer_track(track)

    SNG_TITLE = data['SNG_TITLE']
    ART_NAME = data['ART_NAME']

    try:
        song_filename = format_song_filename(ART_NAME, SNG_TITLE)
        song_path = os.path.join(playlist_dir, song_filename)
        
        # We only support MP3
        if os.path.exists(song_path+'.mp3'):
            return

        download_song(data, song_path)
    except Exception as e:
        print(e)
        return 1

def download_all_playlists():
    user = config['deezer']['user_id']
    result = parse_deezer_user_playlists(user)
    playlists = result['data']

    progress_bar_title = colored('All playlists', 'red')
    with alive_bar(len(playlists), bar='classic2', spinner='waves2', length=50, stats=False, elapsed=False, dual_line=True, monitor='{count}/{total}', title=progress_bar_title) as progress_bar:
        for playlist in playlists:
            tmp_counter = 0
            pl_title = playlist['TITLE']
            pl_nb_song = playlist['NB_SONG']
            pl_id = playlist['PLAYLIST_ID']

            playlist_name, tracks = parse_deezer_playlist(pl_id)
            
            playlist_dir = os.path.join(config['deezer']['music_dir'], 'Playlists', playlist_name.replace(' ', '_'))
            os.makedirs(playlist_dir, exist_ok=True)

            for track in tracks:
                song_title = track['SNG_TITLE']
                artist_name = track['ART_NAME']
                
                song_filename = format_song_filename(artist_name, song_title)
            
                # Download track
                if config["deezer"]["use_hard_links"]:
                    song_download_path = os.path.join(config['deezer']['music_dir'], 'Tracks', song_filename + '.mp3') # Download song to 'Tracks' folder
                    song_final_path = os.path.join(playlist_dir, song_filename + '.mp3')

                    # Skip if file already exits in final playlist folder
                    if os.path.exists(song_final_path):
                        tmp_counter += 1
                        continue
                    elif os.path.exists(song_download_path):
                        # Track exists in 'Tracks' folder, creating hard link to final playlist folder
                        create_song_link(song_download_path, song_final_path)
                    else:
                        # Track not found, downloading it to 'Tracks' folder and creating hard link to final playlist folder
                        try:
                            download_song(track, song_download_path)
                            create_song_link(song_download_path, song_final_path)
                        except Exception as e:
                            tmp_counter += 1
                            pass
                        
                else:
                    song_path = os.path.join(playlist_dir, song_filename + '.mp3')

                    # Skip download if file already exits
                    if os.path.exists(song_path):
                        tmp_counter += 1
                        continue
                
                    try:
                        download_song(track, song_path)
                    except Exception as e:
                        tmp_counter += 1
                        pass
                
                tmp_counter += 1
                download_infos = f" - {tmp_counter}/{pl_nb_song}"
                song_fancy_title = format_song_filename(artist_name, song_title)
                progress_bar.text(' - ' + colored(pl_title, 'blue') + download_infos + ' : ' + colored(song_fancy_title, 'green'))

            progress_bar() # increment progress bar
            print(f"Done downloaded {playlist_name}")