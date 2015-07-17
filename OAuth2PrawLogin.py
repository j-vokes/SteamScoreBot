import requests
import requests.auth
import praw

def redditlogin(prawreddit, clientid, secretkey, user, password):
    client_auth = requests.auth.HTTPBasicAuth(clientid, secretkey)
    post_data = {"grant_type": "password", "username": user, "password": password}
    headers = {"User-Agent": "SteamScoreBot by Avagad"}
    response = requests.post("https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data, headers=headers)
    cred = response.json()
    prawreddit.set_oauth_app_info(client_id=clientid,client_secret=secretkey,redirect_uri='http://127.0.0.1:65010/''authorize_callback')
    scope = set(["identity", "submit", "edit", "modposts"])
    prawreddit.set_access_credentials(scope=scope, access_token=cred["access_token"])
