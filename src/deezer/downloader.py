import os
import deezer.utils as utils
import deezer.songutils as songutils


class Downloader:
    def __init__(self, deezer_client):
        self.client = deezer_client

    def _get_preferred_audio_quality(self, preferred__audio_quality: str) -> list[dict]:
        all_qualities = [
            {"cipher": "BF_CBC_STRIPE", "format": "FLAC"},
            {"cipher": "BF_CBC_STRIPE", "format": "MP3_320"},
            {"cipher": "BF_CBC_STRIPE", "format": "MP3_128"},
            {"cipher": "BF_CBC_STRIPE", "format": "MP3_64"},
        ]

        preferred_qualities = []
        found_selected = False

        for quality in all_qualities:
            if quality["format"] == preferred__audio_quality:
                found_selected = True
            if found_selected:
                preferred_qualities.append(quality)

        return preferred_qualities

    def _get_song_download_infos(self, track_token, prefered_audio_quality, song_id):
        import requests

        api_url = "https://media.deezer.com/v1/get_url"

        license_token = self.client.user_data["licenseToken"]

        payload = {
            "license_token": license_token,
            "media": [
                {
                    "type": "FULL",
                    "formats": self._get_preferred_audio_quality(
                        prefered_audio_quality
                    ),
                }
            ],
            "track_tokens": [track_token],
        }

        req = requests.post(api_url, json=payload)

        if req.status_code != 200:
            print(
                f"Error, received status {req.status_code} when getting download URLs for song {song_id}"
            )
            return None

        rcv_data = req.json()
        data = rcv_data["data"]

        if data and len(data) > 0:
            if "media" not in data[0]:
                if data[0]["errors"]:
                    print(f"Error: {data[0]['errors'][0]['message']}")
                    return None
                else:
                    print(
                        "Error: 'media' item not found when requesting for song download URL"
                    )

            if len(data[0]["media"]) == 0:
                print("Error: No media found")
                return None

            media = data[0]["media"][0]
            media_url = media["sources"][0]["url"]
            media_format = media["format"].lower()

            return {"format": media_format, "url": media_url}

    def _download_song(self, prefered_audio_quality, song_data, output_path):
        import requests
        import deezer.crypto as crypto

        song_title = song_data["SNG_TITLE"]
        artist_name = song_data["ART_NAME"]
        song_id = song_data["SNG_ID"]
        track_token = song_data["TRACK_TOKEN"]
        key = crypto.calcbfkey(song_id)

        # Skip download if song file already exists (mp3)
        song_filename_mp3 = utils.get_song_filename(artist_name, song_title, "mp3")
        output_file_mp3 = os.path.join(output_path, song_filename_mp3)
        if os.path.exists(output_file_mp3):
            return {
                "error": False,
                "output_file_full_path": output_file_mp3,
                "output_file_name": song_filename_mp3,
            }

        # Skip download if song file already exists (flac)
        song_filename_flac = utils.get_song_filename(artist_name, song_title, "flac")
        output_file_flac = os.path.join(output_path, song_filename_flac)
        if os.path.exists(output_file_flac):
            return {
                "error": False,
                "output_file_full_path": output_file_flac,
                "output_file_name": song_filename_flac,
            }

        # Fetch song download URL
        song_infos = self._get_song_download_infos(
            track_token, prefered_audio_quality, song_id
        )

        if not song_infos:
            return {"error": True, "message": "Error: Could not get song download URL"}

        song_media_format = song_infos["format"]
        song_download_url = song_infos["url"]

        # Check for download URL
        if not song_download_url:
            return {
                "error": True,
                "message": f"Error: No download URL for '{song_title} - {artist_name}'",
            }

        # Determine song file extension
        if "mp3" in song_media_format:
            output_file_extension = "mp3"
        elif "flac" in song_media_format:
            output_file_extension = "flac"
        else:
            return {
                "error": True,
                "message": f"Error: Could not determine output file extension, unknown song media format: {song_media_format}",
            }

        song_filename = utils.get_song_filename(
            artist_name, song_title, output_file_extension
        )
        output_file = os.path.join(output_path, song_filename)

        # Download song
        try:
            fh = requests.get(song_download_url)

            if fh.status_code != 200:
                return {
                    "error": True,
                    "mesage": f"Error {fh.status_code}: Could not download '{song_filename}'",
                }

            # create parent dir if dont exists
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            with open(output_file, "w+b") as fo:
                # Add song cover
                songutils.writeid3v2(self.client.session, fo, song_data)
                # Decrypt song file
                crypto.decryptfile(fh, key, fo)
                # Add song metadata
                songutils.writeid3v1_1(fo, song_data)

            return {
                "error": False,
                "output_file_full_path": output_file,
                "output_file_name": song_filename,
            }

        except Exception as e:
            return {
                "error": True,
                "message": f"Error: Could not download {song_filename}\n{str(e)}",
            }
            exit(1)

    def download_favorites(self):
        user_id = self.client.user_data["userId"]

        # Settings
        download_path = self.client.config.get_value("downloads", "music_download_path")
        prefered_audio_quality = self.client.config.get_value(
            "deezer", "prefered_audio_quality"
        )

        # Fetching user's favorites track
        print("Fetching user's favorites track list...")
        favorites_tracks = self.client.api.get_user_favorites_tracks(user_id)
        print(f"Found {len(favorites_tracks)} tracks!")

        if not favorites_tracks:
            print("No tracks found!")
            return

        # Create favorites directory
        favorites_dir = os.path.join(download_path, "Favorites")
        os.makedirs(favorites_dir, exist_ok=True)

        # Create 'Tracks' folder to store all songs if we should use links for duplicates files
        use_links_for_duplicates = self.client.config.get_value(
            "downloads", "use_links_for_duplicates"
        )
        duplicates_links_type = self.client.config.get_value(
            "downloads", "duplicates_link_type"
        )
        tracks_dir = os.path.join(download_path, "Tracks")

        if use_links_for_duplicates:
            os.makedirs(tracks_dir, exist_ok=True)

        # Download songs
        for song in favorites_tracks:
            song_title = song["SNG_TITLE"]
            artist_name = song["ART_NAME"]

            print(
                f"Downloading song: {utils.get_song_filename(artist_name, song_title)}"
            )

            song_file_name = (
                ""  # Full file name will be returned by the "_download_song" function
            )

            # When using links for duplicates
            if use_links_for_duplicates:
                # Download song to 'Tracks' folder
                result = self._download_song(
                    prefered_audio_quality=prefered_audio_quality,
                    song_data=song,
                    output_path=tracks_dir,
                )

                if result["error"]:
                    print(f"Error: {result['message']}. Skipping.")
                    continue

                song_file_path_in_tracks = result["output_file_full_path"]
                song_file_name = result["output_file_name"]
                song_file_path_in_favorites = os.path.join(
                    favorites_dir, song_file_name
                )

                # Create song link from 'Tracks' folder to the 'Favorites' directory
                if not os.path.exists(song_file_path_in_favorites):
                    utils.create_link(
                        src=song_file_path_in_tracks,
                        dest=song_file_path_in_favorites,
                        link_type=duplicates_links_type,
                    )

            # When NOT using links for duplicates
            else:
                # Download song to its playlist folder
                result = self._download_song(
                    prefered_audio_quality=prefered_audio_quality,
                    song_data=song,
                    output_path=album_dir,
                )

                if result["error"]:
                    print(f"Error: {result['message']}. Skipping.")
                    continue

    def download_track(self, download_path, prefered_audio_quality, url):
        print(f"Download track: {url} - {download_path}")

        track_data = self.client.api.get_track_data(url)

        # Track name
        song_title = track_data["SNG_TITLE"]
        artist_name = track_data["ART_NAME"]
        print(f"Downloading track: {utils.get_song_filename(artist_name, song_title)}")

        # Create 'Tracks' directory
        tracks_dir = os.path.join(download_path, "Tracks")
        os.makedirs(tracks_dir, exist_ok=True)

        # Download song to 'Tracks' folder
        result = self._download_song(
            prefered_audio_quality=prefered_audio_quality,
            song_data=track_data,
            output_path=tracks_dir,
        )

        if result["error"]:
            print(f"Error: {result['message']}. Skipping.")

    def download_album(
        self, download_path, prefered_audio_quality, url, allow_single_track_album=True
    ):
        print(f"Download album: {url} - {download_path}")

        album_data = self.client.api.get_album_data(url)

        if len(album_data["data"]) == 0:
            print(f"Error, album: {url} looks empty, skipping")
            return

        # Album infos
        album_name = album_data.get("data", [])[0].get("ALB_TITLE")
        album_id = album_data.get("data", [])[0].get("ALB_ID")
        print(f"Downloading album: {album_name} - {album_id}")

        # Number of songs
        song_count = album_data.get("total")
        if song_count is None:
            print(f"Error: NUMBER_TRACK is {song_count}")
            return

        # Songs
        songs = album_data.get("data", [])
        if not songs:
            print("Error: No songs found")
            return

        is_single_track_album = len(songs) == 1

        # Create album directory
        if not is_single_track_album and not allow_single_track_album:
            sanitized_album_name = utils.sanitize_folder_name(
                name=album_name, item_id=album_id
            )
            album_dir = os.path.join(download_path, "Albums", sanitized_album_name)
            os.makedirs(album_dir, exist_ok=True)

        # Create 'Tracks' folder to store all songs if we should use links for duplicates files
        use_links_for_duplicates = self.client.config.get_value(
            "downloads", "use_links_for_duplicates"
        )
        duplicates_links_type = self.client.config.get_value(
            "downloads", "duplicates_link_type"
        )
        tracks_dir = os.path.join(download_path, "Tracks")

        if use_links_for_duplicates:
            os.makedirs(tracks_dir, exist_ok=True)

        # Download album cover
        if not is_single_track_album and not allow_single_track_album:
            album_cover_id = songs[0]["ALB_PICTURE"]
            album_cover_url = songutils.get_picture_link(album_cover_id)
            album_cover_file = os.path.join(album_dir, "cover.jpg")

            if not os.path.exists(album_cover_file):
                utils.download_image(
                    self.client.session,
                    file_output=album_cover_file,
                    url=album_cover_url,
                )

        # Download songs
        for song in songs:
            song_title = song["SNG_TITLE"]
            artist_name = song["ART_NAME"]

            print(
                f"Downloading song: {utils.get_song_filename(artist_name, song_title)}"
            )

            song_file_name = (
                ""  # Full file name will be returned by the "_download_song" function
            )

            # When using links for duplicates
            if use_links_for_duplicates or (
                is_single_track_album and not allow_single_track_album
            ):
                # Download song to 'Tracks' folder
                result = self._download_song(
                    prefered_audio_quality=prefered_audio_quality,
                    song_data=song,
                    output_path=tracks_dir,
                )

                if result["error"]:
                    print(f"Error: {result['message']}. Skipping.")
                    continue

                if is_single_track_album and not allow_single_track_album:
                    continue

                song_file_path_in_tracks = result["output_file_full_path"]
                song_file_name = result["output_file_name"]
                song_file_path_in_album = os.path.join(album_dir, song_file_name)

                # Create song link from 'Tracks' folder to its album directory
                if not os.path.exists(song_file_path_in_album):
                    utils.create_link(
                        src=song_file_path_in_tracks,
                        dest=song_file_path_in_album,
                        link_type=duplicates_links_type,
                    )

            # When NOT using links for duplicates
            else:
                # Download song to its playlist folder
                result = self._download_song(
                    prefered_audio_quality=prefered_audio_quality,
                    song_data=song,
                    output_path=album_dir,
                )

                if result["error"]:
                    print(f"Error: {result['message']}. Skipping.")
                    continue

    def download_playlist(self, download_path, prefered_audio_quality, url):
        playlist_data = self.client.api.get_playlist_data(url)

        if len(playlist_data["data"]) == 0:
            print(f"Error, playlist: {url} looks empty, skipping")
            return

        # Playlist infos
        playlist_name = playlist_data.get("DATA", {}).get("TITLE")
        playlist_id = playlist_data.get("DATA", {}).get("PLAYLIST_ID")
        print(f"Downloading playlist: {playlist_name} - {playlist_id}")

        # Number of songs
        song_count = playlist_data.get("DATA", {}).get("NB_SONG")
        if song_count is None:
            print(f"Error: NB_SONG is {song_count}")
            return

        # Songs
        songs = playlist_data.get("SONGS", {}).get("data", [])
        if not songs:
            print("Error: No songs found")
            return

        # Create playlist directory
        sanitized_playlist_name = utils.sanitize_folder_name(
            name=playlist_name, item_id=playlist_id
        )
        playlist_dir = os.path.join(download_path, "Playlists", sanitized_playlist_name)
        os.makedirs(playlist_dir, exist_ok=True)

        # Create 'Tracks' folder to store all songs if we should use links for duplicates files
        use_links_for_duplicates = self.client.config.get_value(
            "downloads", "use_links_for_duplicates"
        )
        duplicates_links_type = self.client.config.get_value(
            "downloads", "duplicates_link_type"
        )
        tracks_dir = os.path.join(download_path, "Tracks")

        if use_links_for_duplicates:
            os.makedirs(tracks_dir, exist_ok=True)

        # List of downloaded songs for M3U playlist file
        downloaded_songs = []

        # Download songs
        for song in songs:
            song_title = song["SNG_TITLE"]
            artist_name = song["ART_NAME"]

            print(
                f"Downloading song: {utils.get_song_filename(artist_name, song_title)}"
            )

            song_file_name = (
                ""  # Full file name will be returned by the "_download_song" function
            )

            # When using links for duplicates
            if use_links_for_duplicates:
                # Download song to 'Tracks' folder
                result = self._download_song(
                    prefered_audio_quality=prefered_audio_quality,
                    song_data=song,
                    output_path=tracks_dir,
                )

                if result["error"]:
                    print(f"Error: {result['message']}. Skipping.")
                    continue

                song_file_path_in_tracks = result["output_file_full_path"]
                song_file_name = result["output_file_name"]
                song_file_path_in_playlist = os.path.join(playlist_dir, song_file_name)

                # Create song link from 'Tracks' folder to its playlist directory
                if not os.path.exists(song_file_path_in_playlist):
                    utils.create_link(
                        src=song_file_path_in_tracks,
                        dest=song_file_path_in_playlist,
                        link_type=duplicates_links_type,
                    )

            # When NOT using links for duplicates
            else:
                # Download song to its playlist folder
                result = self._download_song(
                    prefered_audio_quality=prefered_audio_quality,
                    song_data=song,
                    output_path=playlist_dir,
                )

                if result["error"]:
                    print(f"Error: {result['message']}. Skipping.")
                    continue

            # Add song to M3U playlist
            downloaded_songs.append(song_file_name)

        # Generate M3U playlist file
        songutils.generate_playlist_m3u(
            playlist_dir=playlist_dir,
            playlist_name=sanitized_playlist_name,
            songs=downloaded_songs,
        )

    def download_from_url(self, url, prefered_audio_quality=None, download_path=None):
        if not download_path:
            download_path = self.client.config.get_value(
                "downloads", "music_download_path"
            )

        if not prefered_audio_quality:
            prefered_audio_quality = self.client.config.get_value(
                "deezer", "prefered_audio_quality"
            )

        if "track" in url:
            self.download_track(download_path, prefered_audio_quality, url)

        elif "playlist" in url:
            self.download_playlist(download_path, prefered_audio_quality, url)

        elif "album" in url:
            self.download_album(download_path, prefered_audio_quality, url)

        else:
            print("Error: Cannot detect link type")

    def download_all_playlists(self, prefered_audio_quality=None, download_path=None):
        if not download_path:
            download_path = self.client.config.get_value(
                "downloads", "music_download_path"
            )

        if not prefered_audio_quality:
            prefered_audio_quality = self.client.config.get_value(
                "deezer", "prefered_audio_quality"
            )

        user_id = self.client.user_data["userId"]

        # Get user's playlists
        user_playlists = self.client.api.get_user_playlists(user_id)

        # Download each playlist
        for playlist in user_playlists:
            self.download_playlist(
                download_path=download_path,
                prefered_audio_quality=prefered_audio_quality,
                url=playlist[
                    "id"
                ],  # We can also pass an ID because the ID extraction from URL is done using regex
            )

    def download_all_albums(self, prefered_audio_quality=None, download_path=None):
        if not download_path:
            download_path = self.client.config.get_value(
                "downloads", "music_download_path"
            )

        if not prefered_audio_quality:
            prefered_audio_quality = self.client.config.get_value(
                "deezer", "prefered_audio_quality"
            )

        user_id = self.client.user_data["userId"]

        # Get user's albums
        user_albums = self.client.api.get_user_albums(user_id)

        # Download each album
        for album in user_albums:
            self.download_album(
                download_path=download_path,
                prefered_audio_quality=prefered_audio_quality,
                url=album[
                    "id"
                ],  # We can also pass an ID because the ID extraction from URL is done using regex
            )

    def download_all_from_artist(
        self, artist_id, prefered_audio_quality=None, download_path=None
    ):
        if not download_path:
            download_path = self.client.config.get_value(
                "downloads", "music_download_path"
            )

        if not prefered_audio_quality:
            prefered_audio_quality = self.client.config.get_value(
                "deezer", "prefered_audio_quality"
            )

        artist_albums = self.client.api.get_all_artist_albums(artist_id)

        if len(artist_albums) == 0:
            print(f"No album found for artist: {artist_id}, skipping")
            return

        print(f"Downloading {len(artist_albums)} albums from artist...")

        for album_id in artist_albums:
            self.download_album(
                download_path,
                prefered_audio_quality,
                album_id,
                allow_single_track_album=False,
            )

    def download_all_from_favorite_artists(self, user_id=None):
        if not user_id:
            user_id = self.client.user_data["userId"]

        user_favorite_artists = self.client.api.get_user_favorite_artists(user_id)

        if len(user_favorite_artists) == 0:
            print(f"User {user_id} dont have any favorite artist !")
            return

        print(f"Found {len(user_favorite_artists)} artists, downloading...")

        for artist_id in user_favorite_artists:
            print(f"Downloading all from artist {artist_id}")
            self.download_all_from_artist(artist_id)

    def download_all(self):
        self.download_favorites()
        self.download_all_albums()
        self.download_all_playlists()
