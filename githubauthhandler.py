import json
import jwt
import requests
import time
import random
import string
import urllib.parse

from jwt.contrib.algorithms.pycrypto import RSAAlgorithm
try:
    jwt.register_algorithm('RS256', RSAAlgorithm(RSAAlgorithm.SHA256))
except:
    pass

class GHOAuthHandler(object):
    state_set = string.ascii_uppercase+string.digits
    def __init__(self, redirect_uri, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        
    def get_redirect(self, content={}):
        state = { key:val for key,val in content.items() }
        state["__r__"] = "".join(random.choices(self.state_set,k=32))
        state_jwt = jwt.encode(state, self.client_secret, algorithm='HS256').decode()
        params = urllib.parse.urlencode({
            "client_id":self.client_id,
            "redirect_uri":self.redirect_uri,
            "state":state_jwt,
            "scope":"repo"
        })
        return "https://github.com/login/oauth/authorize?"+params
        
    def get_state(self, state):
        decoded = jwt.decode(state, self.client_secret, algorithms='HS256')
        return decoded
        
    def get_token(self, state, code):
        r = requests.session().post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id":self.client_id,
                "client_secret":self.client_secret,
                "code":code,
                "redirect_uri":self.redirect_uri,
                "state":state,
            },
            headers={
                "Accept":"application/json"
            })
        if r.status_code == 200:
            print(r.content)
            return json.loads(r.content)['access_token']
        else:
            raise Exception("{}:{}".format(r.status_code, r.content))

class GHAppAuthHandler(object):
    def __init__(self, github_iss_number, private_key, jwt_durr=600):
        self.private_key = private_key
        self.github_iss_number = github_iss_number
        self.jwt = None
        self.jwt_exp = 0
        self.jwt_durr = jwt_durr
        self.tokens = {}

    def JWT(self, valid_for=0):
        now = int(time.time())
        check_durr = now - self.jwt_exp + valid_for
        if check_durr > self.jwt_durr:
            payload = {
                "iat": now,
                "exp": now + self.jwt_durr,
                "iss": self.github_iss_number
            }
            self.jwt = jwt.encode(
                payload, self.private_key, algorithm='RS256').decode()
            self.jwt_exp = payload["exp"]
        return self.jwt

    def installationToken(self, installation_id, valid_for=0):
        now = int(time.time())
        check_time = now + valid_for
        if (installation_id not in self.tokens) or (
                check_time >= self.tokens[installation_id]['expires_at']):
            url = "https://api.github.com/app/installations/{}/access_tokens".format(
                installation_id)
            print("URL = " + url)
            r = requests.session().post(
                url,
                headers={
                    "Accept":
                    "application/vnd.github.machine-man-preview+json",
                    "Authorization": "Bearer {}".format(self.JWT())
                })
            if r.status_code == 201:
                self.tokens[installation_id] = json.loads(r.content)
                self.tokens[installation_id]['expires_at'] = time.mktime(
                    time.strptime(self.tokens[installation_id]['expires_at'],
                                  "%Y-%m-%dT%H:%M:%SZ"))
            else:
                raise Exception("{}:{}".format(r.status_code, r.content, ))
        return self.tokens[installation_id]['token']
