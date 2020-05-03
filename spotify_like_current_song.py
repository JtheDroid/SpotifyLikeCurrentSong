# import webbrowser
from urllib.parse import urlencode

import appdaemon.plugins.hass.hassapi as hass
import requests


# import application_data


class Spotify:
    statuscode = "_STATUS_CODE_"
    scopes = "user-read-currently-playing user-library-modify"

    def __init__(self, client_id, client_secret,
                 code="", access_token="", refresh_token="", redirect_uri="http://localhost:8888/", print_func=print):
        self.client_id = client_id
        self.client_secret = client_secret
        self.code = code
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.redirect_uri = redirect_uri
        self.authorize_url = "https://accounts.spotify.com/authorize?" + urlencode({"client_id": self.client_id,
                                                                                    "response_type": "code",
                                                                                    "redirect_uri": self.redirect_uri,
                                                                                    "scope": Spotify.scopes})
        self.print = print_func

    def request_token(self, data):
        if "error" in data:
            raise (Exception(data["error"], data["error_description"]))
        else:
            return data["access_token"] if "access_token" in data else "", \
                   data["refresh_token"] if "refresh_token" in data else self.refresh_token

    def request_token_with_auth_code(self, auth_code):
        token_url = "https://accounts.spotify.com/api/token"
        r = requests.post(token_url, data={"grant_type": "authorization_code",
                                           "code": auth_code,
                                           "redirect_uri": self.redirect_uri,
                                           "client_id": self.client_id,
                                           "client_secret": self.client_secret})
        return self.request_token(r.json())

    def request_token_with_refresh_token(self, token):
        token_url = "https://accounts.spotify.com/api/token"
        r = requests.post(token_url, data={"grant_type": "refresh_token",
                                           "refresh_token": token,
                                           "client_id": self.client_id,
                                           "client_secret": self.client_secret})
        return self.request_token(r.json())

    def api_request(self, url, params=None, func=requests.get):
        if params is None:
            params = dict()
        r = func(url, params=params, headers={"Authorization": "Bearer {}".format(self.access_token)})
        data = r.json() if r.content else dict()
        if "error" in data:
            raise Exception("error: " + str(data["error"]))
        data[Spotify.statuscode] = r.status_code
        return data

    def get_currently_playing(self):
        data = self.api_request("https://api.spotify.com/v1/me/player/currently-playing")
        return data["item"]["id"] if "item" in data and "id" in data["item"] else ""

    def like_song(self, song_id):
        if not song_id:
            return
        data = self.api_request("https://api.spotify.com/v1/me/tracks", params={"ids": song_id}, func=requests.put)
        return data

    def auth(self):
        while not self.access_token:
            if self.refresh_token:
                self.access_token, self.refresh_token = self.request_token_with_refresh_token(self.refresh_token)
                self.print("access_token", self.access_token)
                self.print("refresh_token", self.refresh_token)
                return True
            elif self.code:
                self.access_token, self.refresh_token = self.request_token_with_auth_code(self.code)
                self.print("access_token", self.access_token)
                self.print("refresh_token", self.refresh_token)
                return True
            else:
                self.print(self.authorize_url)
                break
        return False
        # webbrowser.open_new_tab(self.authorize_url)
        # self.code = get_callback_code()
        # self.print(self.code)


class SpotifyLikeApp(hass.Hass):

    def initialize(self):
        client_id = self.args["client_id"]
        client_secret = self.args["client_secret"]
        code = self.args["auth_code"] if "auth_code" in self.args else ""
        refresh_token = self.args["refresh_token"] if "refresh_token" in self.args else ""
        self.spotify = Spotify(client_id, client_secret, code=code, refresh_token=refresh_token, print_func=self.log)
        self.token_valid = False
        self.auth()
        self.run_in(self.token_timeout_callback, 3600)
        self.listen_event(self.event_callback, "SPOTIFY_LIKE_CURRENT")

    def auth(self):
        self.token_valid = self.spotify.auth()
        self.run_in(self.token_timeout_callback, 3600)

    def event_callback(self, event_name, data, kwargs):
        if "code" in data:
            self.spotify.code = data["code"]
            self.auth()
        elif not self.token_valid:
            self.auth()
        current_song_id = self.spotify.get_currently_playing()
        self.log(current_song_id)
        self.log(str(self.spotify.like_song(current_song_id)))

    def token_timeout_callback(self, kwargs):
        self.token_valid = False
