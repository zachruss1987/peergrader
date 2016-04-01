import sys, logging
from logging.handlers import RotatingFileHandler
from requests_oauthlib import OAuth2Session
from flask import Flask, request, redirect, session, url_for, render_template, json
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
@app.route('/index')
def root():
    if session.get('username'):
        return redirect(url_for('.github'))
    return render_template('index.html')
    
@app.route('/dashboard')
def dashboard():
    if not session.get('username') or not session.get('fork'):
        return redirect(url_for('.index'))
    build, results = findbuild(session['fork'])
    return results
    return render_template('dashboard.html', username=session['username'], fork=session['fork'], build=build, results=results)
    
def findbuild(fork):
    token = session['oauth_token']['access_token']
    travis = TravisPy.github_auth(token)
    builds = travis.builds(slug=fork, event_type='push')
    if not builds:
        return None, None
    build = builds[0]
    if not build.job_ids:
        return None, None
    jobid = build.job_ids[0]
    job = travis.job(jobid)
    logid = job.log_id
    log = travis.log(logid)
    logged = log.body
    end = logged.rfind('}----------------------------------------------------------------------')
    if end < 1:
        return None, None
    end += 1
    start = logged.rfind('{"stats": {')
    logged = logged[start:end]
    results = json.loads(logged)
    return build, results
    
@app.route('/about')
def about():
    return render_template('about.html')
    
@app.route('/contact')
def contact():
    return render_template('contact.html')
    
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
        
@app.route("/checkfork", methods=["GET"])
def checkfork():
    try:
        token = session['oauth_token']['access_token']
        github = Github(token)
        user = github.get_user()
        session['username'] = user.login
        if session.get('fork'):
            return redirect(url_for('.checktravis'))
        repos = user.get_repos()
        forked = None
        for repo in repos:
            if not repo.fork:
                continue
            parent = repo.parent.full_name
            if parent == HOMEWORK_REPO:
                forked = repo.full_name
                break
        if forked:
            session['fork'] = forked
            return redirect(url_for('.checktravis'))
        else:
            return redirect(url_for('.askfork'))
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        return 'checkfork: %s\n%s\n%s' % (exc_type, exc_value, exc_traceback)
    
@app.route('/askfork')
def askfork():
    return render_template('askfork.html', username=session['username'])
        
@app.route("/dofork", methods=["GET"])
def dofork():
    try:
        token = session['oauth_token']['access_token']
        github = Github(token)
        user = github.get_user()
        repo = github.get_repo(HOMEWORK_REPO)
        fork = user.create_fork(repo)
        return redirect(url_for('.github'))
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        return 'dofork: %s\n%s\n%s' % (exc_type, exc_value, exc_traceback)
        
@app.route("/checktravis", methods=["GET"])
def checktravis():
    try:
        if not session.get('fork') or not session.get('username'):
            return redirect(url_for('.github'))
        token = session['oauth_token']['access_token']
        travis = TravisPy.github_auth(token)
        username = session['username']
        repos = travis.repos(member=username)
        verified = False
        for repo in repos:
            if session['fork'].lower() == repo.slug.lower():
                verified = True
                break
        if verified:
            return redirect(url_for('.dashboard'))
        else:
            return redirect(url_for('.asktravis'))
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        return 'checktravis: %s\n%s\n%s' % (exc_type, exc_value, exc_traceback)
    
@app.route('/asktravis')
def asktravis():
    return render_template('asktravis.html', username=session['username'], fork=session['fork'])

if __name__ == '__main__':
    app.run()
    
