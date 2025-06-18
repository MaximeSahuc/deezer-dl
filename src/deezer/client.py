import json
import requests

from deezer.api import Api
from deezer.downloader import Downloader


class DeezerClient:
    def __init__(self, config_manager):
        self.config = config_manager
        self.session = None
        self.user_data = []
        self.api = Api(deezer_client=self)
        self.arl_cookie = self.config.get_value("deezer", "arl_cookie")
        self.downloader = Downloader(deezer_client=self)
        self._init_session()
        self._fetch_csrf_token_and_user_data()

    def _init_session(self):
        header = {
            "Pragma": "no-cache",
            "Origin": "https://www.deezer.com",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "*/*",
            "Cache-Control": "no-cache",
            "X-Requested-With": "XMLHttpRequest",
            "Connection": "keep-alive",
            "Referer": "https://www.deezer.com/login",
            "DNT": "1",
        }

        self.session = requests.session()
        self.session.headers.update(header)
        self.session.cookies.update({"arl": self.arl_cookie, "comeback": "1"})

    def _fetch_csrf_token_and_user_data(self):
        api_url = "https://www.deezer.com/ajax/gw-light.php?method=deezer.getUserData&input=3&api_version=1.0&api_token="
        print("Fetching CSRF token and user data...")

        try:
            # requests automatically handles JSON encoding for the 'json' parameter
            response = self.session.post(api_url, json={})

            response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)

            data = response.json()

            if not data or not data.get("results"):
                if data.get("error") and len(data["error"]) > 0:
                    error_message = (
                        ", ".join(data["error"])
                        if isinstance(data["error"], list)
                        else data["error"]
                    )
                    print(f"Deezer User Data API returned an error: {error_message}")
                    raise Exception(f"Deezer API error: {error_message}")
                raise Exception("User Data API response missing 'results' field.")

            results = data["results"]
            csrf_token = results.get("checkForm")
            user_options = results.get("USER", {}).get("OPTIONS", {})
            country = user_options.get("license_country")
            license_token = user_options.get("license_token")
            user_id = results.get("USER", {}).get("USER_ID")

            if not csrf_token:
                if data.get("error") and len(data["error"]) > 0:
                    error_message = (
                        ", ".join(data["error"])
                        if isinstance(data["error"], list)
                        else data["error"]
                    )
                    print(
                        f"Deezer User Data API returned an error (missing CSRF): {error_message}"
                    )
                    raise Exception(f"Deezer API error (missing CSRF): {error_message}")
                raise Exception("CSRF token (checkForm) not found in API response.")

            final_country = country
            if not final_country:
                fallback_country = results.get("COUNTRY")
                if not fallback_country:
                    print("Could not determine user country from API response.")
                    print("Could not determine user country from API response.")
                    final_country = "us"
                else:
                    print(f"Using fallback country: {fallback_country}")
                    print(f"Using fallback country: {fallback_country}")
                    final_country = fallback_country

            if user_id is None:
                print("User ID not found in API response.")
                print("User ID not found in API response.")
            if license_token is None:
                print("License Token not found in API response.")
                print("License Token not found in API response.")

            print(
                f"CSRF Token: {'Found' if csrf_token else 'Not Found'} | Country: {final_country} | UserID: {user_id or 'N/A'} | License Token: {'Found' if license_token else 'Not Found'}\n\n"
            )

            self.user_data = {
                "csrfToken": csrf_token,
                "country": final_country.lower(),
                "userId": user_id,
                "licenseToken": license_token,
            }

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error fetching user data/CSRF token: {http_err}")
            raise Exception(
                f"HTTP error fetching user data! Status: {http_err.response.status_code}"
            ) from http_err
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Connection error fetching user data/CSRF token: {conn_err}")
            raise Exception(
                f"Connection error fetching user data! Error: {conn_err}"
            ) from conn_err
        except requests.exceptions.Timeout as timeout_err:
            print(f"Timeout error fetching user data/CSRF token: {timeout_err}")
            raise Exception(
                f"Timeout error fetching user data! Error: {timeout_err}"
            ) from timeout_err
        except requests.exceptions.RequestException as req_err:
            print(f"Error fetching user data/CSRF token: {req_err}")
            raise Exception(
                f"Error during request to Deezer API: {req_err}"
            ) from req_err
        except json.JSONDecodeError as json_err:
            print(f"JSON decode error: {json_err}")
            raise Exception(
                f"Failed to decode JSON response from Deezer API: {json_err}"
            ) from json_err
        except Exception as err:
            print(f"Error fetching user data/CSRF token: {err}")
            raise err

    def request_api(self, request_type, method, post_data=None, json_data=None):
        csrf_token = self.user_data["csrfToken"]

        match request_type:
            case "GET":
                print("GET api requests are not implemented yet")
                pass

            case "POST":
                url = f"https://www.deezer.com/ajax/gw-light.php?method={method}&input=3&api_version=1.0&api_token={csrf_token}"

                if post_data:
                    response = self.session.post(url, data=post_data)
                elif json_data:
                    response = self.session.post(url, json=json_data)
                else:
                    response = self.session.post(url)

                if response.status_code != 200:
                    print(
                        f"Error: received status {response.status_code} for {method} method"
                    )

                    return None

                if response.json() and response.json()["error"]:
                    if len(response.json()["error"]):
                        if "NEED_USER_AUTH_REQUIRED" in response.json()["error"]:
                            print(
                                "\nError: Invalid credentials. Please check your config file."
                            )
                            exit(1)

                        print(f"Error: {response.json()['error']}")

                    return None

                return response.json()

            case _:
                print("Invalid request type")
                return None

    def get_user(self):
        return self.user_data

    def get_downloader(self):
        return self.downloader

    def export_all_user_data(self, user_id=None):
        import os
        from deezer.utils import write_to_json, sanitize_folder_name

        if not user_id:
            user_id = self.user_data["userId"]

        user_infos = self.api.get_user_infos(user_id)
        if not user_infos:
            print("User not found!")
            exit(1)

        DEBUG_DATA_DIR = os.path.join(
            os.path.expanduser("~"), ".deezer-dl", "user-data", user_infos["name"]
        )

        print(f"Starting user data export for user: {user_infos['name']}")

        # Export user infos
        print("Exporting user infos...")
        write_to_json(DEBUG_DATA_DIR, "user_infos.json", user_infos)

        # Dump user's favorite tracks
        print("Exporting favorite tracks...")
        user_favorite_tracks = self.api.get_user_favorites_tracks(user_id)
        if user_favorite_tracks:
            write_to_json(DEBUG_DATA_DIR, "favorite_tracks.json", user_favorite_tracks)

        # Dump user's playlists
        print("Dumping user's playlists...")
        user_playlists = self.api.get_user_playlists(user_id)
        playlist_data_dir = os.path.join(DEBUG_DATA_DIR, "playlists")
        if user_playlists:
            for playlist in user_playlists:
                print(f"Dumping playlist: {playlist['name']}")
                playlist_data = self.api.get_playlist_data(playlist["id"])
                sanitized_playlist_name = sanitize_folder_name(
                    playlist["name"], playlist["id"]
                )
                write_to_json(
                    playlist_data_dir, f"{sanitized_playlist_name}.json", playlist_data
                )

        # Dump user's saved albums
        print("Dumping user's saved albums...")
        user_albums = self.api.get_user_albums(user_id)
        album_data_dir = os.path.join(DEBUG_DATA_DIR, "albums")
        if user_albums:
            for album in user_albums:
                print(f"Dumping album: {album['name']}")
                album_data = self.api.get_album_data(album["id"])
                sanitized_album_name = sanitize_folder_name(album["name"], album["id"])
                write_to_json(
                    album_data_dir, f"{sanitized_album_name}.json", album_data
                )

        # Dump user's favotite artists
        print("Dumping user's favorite artists")
        user_favorite_artists = self.api.get_user_favorite_artists(user_id)
        if user_favorite_artists:
            write_to_json(
                DEBUG_DATA_DIR, "favorite_artists.json", user_favorite_artists
            )

        print("\nDone!")
        print(f"Data location: {DEBUG_DATA_DIR}")
