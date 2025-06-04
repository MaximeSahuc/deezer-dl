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

    def get_user_favorite_tracks(self, user_id):
        pass

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

    def get_users_page_profile(self, tab):
        payload = {"USER_ID": self.client.user_data["userId"], "tab": tab, "nb": 10000}

        json_response = self.client.request_api(
            "POST", "deezer.pageProfile", post_data=json.dumps(payload)
        )
        if not json_response:
            raise

        if json_response["results"]["TAB"][tab]:
            if len(json_response["results"]["TAB"][tab]["data"]) > 0:
                return json_response["results"]["TAB"][tab]["data"]
            else:
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
