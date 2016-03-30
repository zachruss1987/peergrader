import sys, logging
from logging.handlers import RotatingFileHandler
from requests_oauthlib import OAuth2Session
from flask import Flask, request, redirect, session, url_for
from flask.json import jsonify
from pymongo import MongoClient
from travispy import TravisPy
from github import Github

import secrets

app = Flask(__name__, static_url_path='')
app.secret_key = secrets.COOKIE_KEY
handler = RotatingFileHandler('/home/ct/peergrader.log', maxBytes=100000, backupCount=5)
handler.setLevel(logging.WARNING)
app.logger.addHandler(handler)

BASE_URL = 'https://peergrader.ctgraham.com'
AUTHORIZE_URL = 'https://github.com/login/oauth/authorize'
TOKEN_URL = 'https://github.com/login/oauth/access_token'
SCOPES = ['read:org', 'user:email', 'repo_deployment', 'repo:status', 'write:repo_hook', 'public_repo']
HOMEWORK_REPO = 'chrisgtech/peergrader'

@app.route('/')
def root():
    return app.send_static_file('index.html')
    
@app.route('/github')
def github():
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

        return redirect(url_for('.checkfork'))
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
        
@app.route("/checkfork", methods=["GET"])
def checkfork():
    try:
        token = session['oauth_token']['access_token']
        github = Github(token)
        user = github.get_user()
        repos = user.get_repos()
        forked = False
        for repo in repos:
            if not repo.fork:
                continue
            parent = repo.parent.full_name
            if parent == HOMEWORK_REPO:
                forked = True
                break
        if forked:
            return 'Fork already exists'
        else:
            return redirect(url_for('.dofork'))
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        return 'forks: %s\n%s\n%s' % (exc_type, exc_value, exc_traceback)
        
@app.route("/dofork", methods=["GET"])
def dofork():
    try:
        token = session['oauth_token']['access_token']
        github = Github(token)
        user = github.get_user()
        repo = github.get_repo(HOMEWORK_REPO)
        fork = user.create_fork(repo)
        output = 'Fork %s created from %s' % (fork.full_name, HOMEWORK_REPO)
        return output
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        return 'dofork: %s\n%s\n%s' % (exc_type, exc_value, exc_traceback)
        
@app.route("/travis", methods=["GET"])
def travis():
    try:
        token = session['oauth_token']['access_token']
        travis = TravisPy.github_auth(token)
        username = travis.user().login
        repos = travis.repos(member=username)
        return repos[0].slug
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        return 'travis: %s\n%s\n%s' % (exc_type, exc_value, exc_traceback)

if __name__ == '__main__':
    app.run()
    
