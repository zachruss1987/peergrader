import sys, logging
from logging.handlers import RotatingFileHandler
from requests_oauthlib import OAuth2Session
from flask import Flask, request, redirect, session, url_for
from flask.json import jsonify
from pymongo import MongoClient

import secrets

app = Flask(__name__)
app.secret_key = secrets.COOKIE_KEY
handler = RotatingFileHandler('/home/ct/peergrader.log', maxBytes=100000, backupCount=5)
handler.setLevel(logging.WARNING)
app.logger.addHandler(handler)

BASE_URL = 'https://peergrader.ctgraham.com'
AUTHORIZE_URL = 'https://github.com/login/oauth/authorize'
TOKEN_URL = 'https://github.com/login/oauth/access_token'
SCOPES = ['read:org', 'user:email', 'repo_deployment', 'repo:status', 'write:repo_hook', 'public_repo']

@app.route('/')
def index():
    try:
        authorizer = BASE_URL + url_for('.authorize')
        github = OAuth2Session(secrets.CLIENT_ID, redirect_uri=authorizer, scope=SCOPES)
        authorization_url, state = github.authorization_url(AUTHORIZE_URL)
        session['oauth_state'] = state
        return redirect(authorization_url)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        return 'index: %s\n%s\n%s' % (exc_type, exc_value, exc_traceback)

@app.route('/data')
def names():
    data = {"names": ["John", "Jacob", "Julie", "Jennifer"]}
    return jsonify(data)
    
@app.route('/authorize', methods=["GET"])
def authorize():
    try:
        requested = request.url.replace('http', 'https')
        github = OAuth2Session(secrets.CLIENT_ID, state=session['oauth_state'])
        token = github.fetch_token(TOKEN_URL, client_secret=secrets.CLIENT_SECRET,
                                   authorization_response=requested)

        session['oauth_token'] = token

        return redirect(url_for('.profile'))
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        return 'authorize: %s\n%s %s\n%s' % (exc_type, exc_value, requested, exc_traceback)
    
@app.route("/profile", methods=["GET"])
def profile():
    """Fetching a protected resource using an OAuth 2 token.
    """
    try:
        github = OAuth2Session(secrets.CLIENT_ID, token=session['oauth_token'])
        return jsonify(github.get('https://api.github.com/user').json()) 
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        return 'profile: %s\n%s\n%s' % (exc_type, exc_value, exc_traceback)

if __name__ == '__main__':
    app.run()
    
