import sys, logging, time, base64, hashlib, hmac, json
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
DISQUS_AUTHORIZE = 'https://disqus.com/api/oauth/2.0/authorize/'
DISQUS_TOKEN = 'https://disqus.com/api/oauth/2.0/access_token/'
HOMEWORK_REPO = 'chrisgtech/peergrader'

@app.route('/')
@app.route('/index')
def root():
    if session.get('username'):
        return redirect(url_for('.github'))
    return render_template('index.html')
    
@app.route('/dashboard')
def dashboard():
    github, travis = loadapis()
    if not github or not travis:
        return redirect(url_for('.root'))
    build, results = findbuild(travis, session['fork'])
    submission, latest = findsubmission(github, session['fork'])
    return render_template('dashboard.html', username=session['username'], fork=session['fork'], build=build, results=results, submission=submission, latest=latest)
    
@app.route('/review')
def review():
    github, travis = loadapis()
    if not github or not travis:
        return redirect(url_for('.root'))
    submission, latest = findsubmission(github, session['fork'])
    build, results = None, None
    if submission:
        build, results = findbuild(travis, session['fork'], submission)
    return render_template('review.html', username=session['username'], fork=session['fork'], build=build, results=results, submission=submission, latest=latest)

@app.route('/discuss')
def discuss():
    github, travis = loadapis()
    if not github or not travis:
        return redirect(url_for('.dashboard'))
    build, results = findbuild(travis, session['fork'])
    testname = request.args.get('test')
    test = None
    for result in results['results']:
        if result['name'] == testname:
            test = result
            break
    if not test or test['type'] == 'success':
        return redirect(url_for('.dashboard'))
    trace = test['tb']
    trace = trace.replace(session['username'], 'user')
    hashed = hashlib.sha256('%s %s' % (test['name'], trace)).hexdigest()
    slug = 'error_%s' % hashed
    details = {'id':'peergrader_user_%s' % session['username'], 'username':session['username'], 'email':session['useremail']}
    jsoned = json.dumps(details)
    message = base64.b64encode(jsoned)
    timestamp = int(time.time())
    sig = hmac.HMAC(secrets.DISQUS_SECRET, '%s %s' % (message, timestamp), hashlib.sha1).hexdigest()
    data = '%s %s %s' % (message, sig, timestamp)
    return render_template('discuss.html', test=test, public_key=secrets.DISQUS_PUBLIC, message=data, slug=slug)
    
def findbuild(travis, fork, sha=None):
    builds = travis.builds(slug=fork, event_type='push')
    if not builds:
        return None, None
    build = builds[0]
    if sha:
        build = None
        for record in builds:
            if sha == record.commit.sha:
                build = record
                break
    if not build or not build.job_ids:
        return None, None
    jobid = build.job_ids[0]
    job = travis.job(jobid)
    logid = job.log_id
    log = travis.log(logid)
    logged = log.body
    end = logged.rfind('}----------------------------------------------------------------------')
    if end < 1:
        return logged, None
    end += 1
    start = logged.rfind('{"stats": {')
    logged = logged[start:end]
    results = json.loads(logged)
    return build, results
    
def findsubmission(github, fork):
    if not session.get('username') or not session.get('fork'):
        return None
    repo = github.get_repo(fork)
    refs = repo.get_git_refs()
    submission, latest = None, None
    for ref in refs:
        name = ref.ref
        if name == 'refs/heads/master':
            latest = ref.object.sha
        elif name == 'refs/heads/submitted':
            submission = ref.object.sha
    return submission, latest
    
def loadapis():
    if not session.get('username') or not session.get('fork'):
        return None, None
    token = session['oauth_token']['access_token']
    github, travis = None, None
    try:
        github = Github(token)
        travis = TravisPy.github_auth(token)
    except:
        return None, None
    return github, travis
    
@app.route('/about')
def about():
    return render_template('about.html')
    
@app.route('/contact')
def contact():
    return render_template('contact.html')
    
@app.route('/terms')
def terms():
    return render_template('terms.html')
    
@app.route('/privacy')
def privacy():
    return render_template('privacy.html')
    
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
        return 'github: %s\n%s\n%s' % (exc_type, exc_value, exc_traceback)
    
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
    
#@app.route('/disqus')
#def disqus():
#    try:
#        #authorizer = BASE_URL + url_for('.authorize')
#        #auth = OAuth2Session(secrets.DISQUS_PUBLIC, redirect_uri=authorizer, scope=SCOPES)
#        auth = OAuth2Session(secrets.DISQUS_PUBLIC)
#        authorization_url, state = auth.authorization_url(DISQUS_AUTHORIZE)
#        session['oauth_state'] = state
#        return redirect(authorization_url)
#    except:
#        exc_type, exc_value, exc_traceback = sys.exc_info()
#        return 'disqus: %s\n%s\n%s' % (exc_type, exc_value, exc_traceback)
#    
#@app.route('/authd', methods=["GET"])
#def authd():
#    try:
#        requested = request.url.replace('http', 'https')
#        #github = OAuth2Session(secrets.DISQUS_PUBLIC, state=session['oauth_d'])
#        github = OAuth2Session(secrets.DISQUS_PUBLIC)
#        token = github.fetch_token(DISQUS_TOKEN, client_secret=secrets.DISQUS_PUBLIC,
#                                   authorization_response=requested)
#
#        session['token_d'] = token
#        return redirect(url_for('.discuss'))
#    except:
#        exc_type, exc_value, exc_traceback = sys.exc_info()
#        return 'authd: %s\n%s %s\n%s' % (exc_type, exc_value, requested, exc_traceback)
        
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
        session['fork'] = fork.full_name
        return redirect(url_for('.github'))
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        return 'dofork: %s\n%s\n%s' % (exc_type, exc_value, exc_traceback)
        
@app.route("/dosubmit", methods=["GET"])
def dosubmit():
    try:
        refname = 'refs/heads/submitted'
        github, ignored = loadapis()
        submission, latest = findsubmission(github, session['fork'])
        if not github or not latest:
            return redirect(url_for('.root'))
        repo = github.get_repo(session['fork'])
        refs = repo.get_git_refs()
        subref = None
        for ref in refs:
            name = ref.ref
            if name == refname:
                subref = ref
        if not subref:
            subref = repo.create_git_ref(refname, latest)
        else:
            subref.edit(latest, True)
        return redirect(url_for('.dashboard'))
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
        user = travis.user()
        session['useremail'] = user.email
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
        if 'Forbidden' in str(exc_value):
            session['username'] = None
            return redirect(url_for('.root'))
        return 'checktravis: %s\n%s\n%s' % (exc_type, exc_value, exc_traceback)
    
@app.route('/asktravis')
def asktravis():
    return render_template('asktravis.html', username=session['username'], fork=session['fork'])
    
@app.route('/testing')
def testing():
    github, travis = loadapis()
    fork = session['fork']
    build, results = findbuild(travis, fork)
    newbuild = build.commit.sha
    submit, latest = findsubmission(github, fork)
    build, results = findbuild(travis, fork, submit)
    oldbuild = build.commit.sha
    return '%s - %s - %s - %s' % (latest, submit, newbuild, oldbuild)

if __name__ == '__main__':
    app.run()
    
