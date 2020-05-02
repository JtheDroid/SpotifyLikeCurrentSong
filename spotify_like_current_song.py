import webbrowser
from urllib.parse import urlencode

import requests

from application_data import client_id, client_secret
from http_server import get_callback_code

statuscode = "_STATUS_CODE_"
scopes = "user-read-currently-playing user-library-modify"
redirect_uri = "http://localhost:8888/"
authorize_url = "https://accounts.spotify.com/authorize?" + urlencode({"client_id": client_id,
                                                                       "response_type": "code",
                                                                       "redirect_uri": redirect_uri,
                                                                       "scope": scopes})

code = ""
access_token = ""
refresh_token = ""


def request_token(data):
    if "error" in data:
        raise (Exception(data["error"], data["error_description"]))
    else:
        return data["access_token"] if "access_token" in data else "", \
               data["refresh_token"] if "refresh_token" in data else refresh_token


def request_token_with_auth_code(auth_code):
    token_url = "https://accounts.spotify.com/api/token"
    r = requests.post(token_url, data={"grant_type": "authorization_code",
                                       "code": auth_code,
                                       "redirect_uri": redirect_uri,
                                       "client_id": client_id,
                                       "client_secret": client_secret})
    return request_token(r.json())


def request_token_with_refresh_token(token):
    token_url = "https://accounts.spotify.com/api/token"
    r = requests.post(token_url, data={"grant_type": "refresh_token",
                                       "refresh_token": token,
                                       "client_id": client_id,
                                       "client_secret": client_secret})
    return request_token(r.json())


def api_request(url, params=None, func=requests.get):
    if params is None:
        params = dict()
    r = func(url, params=params, headers={"Authorization": "Bearer {}".format(access_token)})
    data = r.json() if r.content else dict()
    if "error" in data:
        raise Exception("error: " + str(data["error"]))
    data[statuscode] = r.status_code
    return data


def get_currently_playing():
    data = api_request("https://api.spotify.com/v1/me/player/currently-playing")
    return data["item"]["id"] if "item" in data and "id" in data["item"] else ""


def like_song(song_id):
    if not song_id:
        return
    data = api_request("https://api.spotify.com/v1/me/tracks", params={"ids": song_id}, func=requests.put)
    return data


while not access_token:
    if refresh_token:
        access_token, refresh_token = request_token_with_refresh_token(refresh_token)
        print("access_token", access_token)
        print("refresh_token", refresh_token)

    elif code:
        access_token, refresh_token = request_token_with_auth_code(code)
        print("access_token", access_token)
        print("refresh_token", refresh_token)

    else:
        webbrowser.open_new_tab(authorize_url)
        code = get_callback_code()
        print(code)

current_song_id = get_currently_playing()
print(current_song_id)
print(like_song(current_song_id))
