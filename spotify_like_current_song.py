import base64
from urllib.parse import urlencode
from http_server import get_callback_code

import requests
import webbrowser
from application_data import client_id, client_secret

scopes = "user-read-currently-playing user-library-modify"
redirect_uri = "http://localhost:8888/"
authorize_url = "https://accounts.spotify.com/authorize?" + urlencode({"client_id": client_id,
                                                                       "response_type": "code",
                                                                       "redirect_uri": redirect_uri,
                                                                       "scope": scopes})

code = ""
access_token = ""
refresh_token = ""


def request_token(request):
    json_data = request.json()
    print(json_data)
    if "error" in json_data:
        print("Error:", json_data["error"], json_data["error_description"])
        raise (Exception(json_data["error"], json_data["error_description"]))
    else:
        print("access_token", json_data["access_token"])
        print("refresh_token", json_data["refresh_token"])
        return json_data["access_token"], json_data["refresh_token"]


def request_token_with_auth_code(auth_code):
    token_url = "https://accounts.spotify.com/api/token"
    r = requests.post(token_url, data={"grant_type": "authorization_code",
                                       "code": auth_code,
                                       "redirect_uri": redirect_uri,
                                       "client_id": client_id,
                                       "client_secret": client_secret})
    return request_token(r)


def request_token_with_refresh_token(token):
    token_url = "https://accounts.spotify.com/api/token"
    r = requests.post(token_url, data={"grant_type": "refresh_token",
                                       "refresh_token": token,
                                       "client_id": client_id,
                                       "client_secret": client_secret})
    return request_token(r)


def api_request(url, args=None, func=requests.get):
    if args is None:
        args = dict()
    r = func(url, data=args, headers={"Authorization": "Bearer {}".format(access_token)})
    data = r.json() if r.content else dict()
    if "error" in data:
        raise Exception("error: " + str(data["error"]))
    return data


def get_currently_playing():
    data = api_request("https://api.spotify.com/v1/me/player/currently-playing")
    return data["item"]["id"] if "item" in data and "id" in data["item"] else ""


while not access_token:
    if refresh_token:
        access_token, refresh_token = request_token_with_refresh_token(refresh_token)
        print(access_token, refresh_token)

    elif code:
        access_token, refresh_token = request_token_with_auth_code(code)
        print(access_token, refresh_token)

    else:
        webbrowser.open_new_tab(authorize_url)
        code = get_callback_code()
        print(code)

print(get_currently_playing())
