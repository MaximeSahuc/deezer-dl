import json
import deezer.utils as utils


class Api:
    def __init__(self, deezer_client):
        self.client = deezer_client

    def get_user_favorites_tracks(self, user_id):
        next_url = f"https://api.deezer.com/user/{user_id}/tracks?limit=10000000000"

        # Fetch all tracks ID
        tracks_list = []
        while True:
            response = self.client.session.get(next_url)
            json_data = response.json()

            tracks = json_data["data"]

            if not tracks:
                return tracks_list

            for track in tracks:
                tracks_list.append(track["id"])

            if "next" in json_data:
                next_url = json_data["next"]
                continue

            break

        # Fetch tracks data
        tracks = []
        payload = {"sng_ids": tracks_list}

        response = self.client.request_api(
            request_type="POST",
            method="song.getListData",
            json_data=payload,
        )

        if len(response["error"]) > 0:
            print(f"Error: deezer API response: {response['error']}")
            return None

        return response["results"]["data"]

    def get_user_favorite_artists(self, user_id):
        next_url = f"https://api.deezer.com/user/{user_id}/artists?limit=10000000000"

        # Fetch all artists ID
        artists_list = []
        while True:
            response = self.client.session.get(next_url)
            json_data = response.json()

            artists = json_data["data"]

            if not artists:
                return artists_list

            for artist in artists:
                artists_list.append({"id": artist["id"], "name": artist["name"]})

            if "next" in json_data:
                next_url = json_data["next"]
                continue

            break

        return artists_list

    def get_all_artist_albums(self, artist_id):
        artist_id = utils.extract_id_from_url(artist_id)

        next_url = f"https://api.deezer.com/artist/{artist_id}/albums?limit=10000000000"

        # Fetch all albums ID
        albums_list = []
        while True:
            response = self.client.session.get(next_url)
            json_data = response.json()

            albums = json_data["data"]

            if not albums:
                return albums_list

            for album in albums:
                albums_list.append({"id": album["id"], "name": album["title"]})

            if "next" in json_data:
                next_url = json_data["next"]
                continue

            break

        return albums_list

    def get_user_infos(self, user_id):
        url = f"https://api.deezer.com/user/{user_id}/"

        response = self.client.session.get(url)

        if response.ok:
            return response.json()

        return None

    def get_album_infos(self, playlist_id):
        url = f"https://api.deezer.com/album/{playlist_id}/"

        response = self.client.session.get(url)

        if response.ok:
            return response.json()

        return None

    def get_track_data(self, url):
        track_id = utils.extract_id_from_url(url)

        if not track_id:
            print(f"Error: could not find track id in URL: {url}")
            return None

        payload = {"sng_ids": [track_id]}

        response = self.client.request_api(
            request_type="POST",
            method="song.getListData",
            json_data=payload,
        )

        if len(response["error"]) > 0:
            print(f"Error: deezer API response: {response['error']}")
            return None

        return response["results"]["data"][0]

    def get_album_data(self, url):
        album_id = utils.extract_id_from_url(url)

        if not album_id:
            print(f"Error: could not find album id in URL: {url}")
            return None

        payload = {
            "alb_id": int(album_id),
            "start": 0,
            "nb": 500,
        }

        response = self.client.request_api(
            request_type="POST",
            method="song.getListByAlbum",
            json_data=payload,
        )

        if len(response["error"]) > 0:
            print(f"Error: deezer API response: {response['error']}")
            return None

        return response["results"]

    def get_playlist_data(self, url):
        playlist_id = utils.extract_id_from_url(url)

        if not playlist_id:
            print(f"Error: could not find playlist id in URL: {url}")
            return None

        payload = {
            "playlist_id": int(playlist_id),
            "start": 0,
            "tab": 0,
            "header": True,
            "lang": self.client.user_data["country"],
            "nb": -1,
        }

        response = self.client.request_api(
            request_type="POST",
            method="deezer.pagePlaylist",
            json_data=payload,
        )

        if len(response["error"]) > 0:
            print(f"Error: deezer API response: {response['error']}")
            return None

        return response["results"]

    def get_user_notifications(self):
        json_response = self.client.request_api("POST", "deezer.userMenu")
        if not json_response:
            raise

        if json_response["results"] and json_response["results"]["NOTIFICATIONS"]:
            return json_response["results"]["NOTIFICATIONS"]["data"]
        else:
            print("Error: no notifications found")
            return

    def mark_notification_as_read(self, notification_ids):
        self.client.request_api(
            "POST", "notification.markAsRead", post_data={"notif_ids": notification_ids}
        )

    def get_users_page_profile(self, tab, user_id=None):
        if not user_id:
            user_id = self.client.user_data["userId"]

        payload = {"USER_ID": user_id, "tab": tab, "nb": 10000}

        json_response = self.client.request_api(
            "POST", "deezer.pageProfile", post_data=json.dumps(payload)
        )
        if not json_response:
            raise

        if json_response["results"]["TAB"][tab]:
            if len(json_response["results"]["TAB"][tab]["data"]) > 0:
                return json_response["results"]["TAB"][tab]["data"]
            else:
                print("Error: no data found!")
                return []
        else:
            print(f"Error: no {tab} found")
            return []

    def follow_user(self, user_id):
        payload = {"friend_id": user_id, "ctxt": {"id": user_id, "t": "profile_page"}}

        json_response = self.client.request_api(
            "POST", "friend.follow", post_data=json.dumps(payload)
        )
        if not json_response:
            raise

        if json_response["results"]:
            return json_response["results"]
        else:
            print(f"Error: cannot follow user {user_id} found")
            raise

    def get_user_playlists(self, user_id):
        playlists = self.get_users_page_profile(tab="playlists", user_id=user_id)
        playlists = list(
            [
                {"name": playlist["TITLE"], "id": playlist["PLAYLIST_ID"]}
                for playlist in playlists
                if playlist["__TYPE__"] == "playlist"
                and playlist["PARENT_USER_ID"] == str(user_id)
            ]
        )

        return playlists

    def get_user_albums(self, user_id):
        albums = self.get_users_page_profile(tab="albums", user_id=user_id)
        albums = list(
            [
                {"name": playlist["ALB_TITLE"], "id": playlist["ALB_ID"]}
                for playlist in albums
                if playlist["__TYPE__"] == "album"
            ]
        )

        return albums
