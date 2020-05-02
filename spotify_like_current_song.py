import webbrowser
from urllib.parse import urlencode

import requests

import application_data
from http_server import get_callback_code


class Spotify:
    statuscode = "_STATUS_CODE_"
    scopes = "user-read-currently-playing user-library-modify"

    def __init__(self, client_id, client_secret,
                 code="", access_token="", refresh_token="", redirect_uri="http://localhost:8888/"):
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
                print("access_token", self.access_token)
                print("refresh_token", self.refresh_token)
            elif self.code:
                self.access_token, self.refresh_token = self.request_token_with_auth_code(self.code)
                print("access_token", self.access_token)
                print("refresh_token", self.refresh_token)
            else:
                webbrowser.open_new_tab(self.authorize_url)
                self.code = get_callback_code()
                print(self.code)


s = Spotify(application_data.client_id, application_data.client_secret)
s.auth()
current_song_id = s.get_currently_playing()
print(current_song_id)
print(s.like_song(current_song_id))
