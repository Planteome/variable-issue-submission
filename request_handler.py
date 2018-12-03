from flask import Flask, request, send_from_directory, make_response, redirect, render_template, jsonify
from jinja2 import Environment, FunctionLoader
from functools import wraps, update_wrapper
from datetime import datetime
import json
import sqlite3
import requests
import databasefunctions as db
from githubauthhandler import GHAppAuthHandler, GHOAuthHandler
import zipfile
import io
import urllib.parse
from pathlib import Path
import os.path

# file loader (for config file)
def load(name):
    with open(name) as fi:
        return fi.read()
        
# Flask app setup
app = Flask(__name__)

# config
with open("config.json") as conf_file:
    config = json.load(conf_file);
pkey = Path(config['skey']).read_text()

# Setup for GitHub App
ah = GHAppAuthHandler(config['iss'], pkey)
# Setup for GitHub OAuth
oauth_path = "/authorized/oauth"
auth_url = urllib.parse.urljoin(config['base_url'], oauth_path)
oh = GHOAuthHandler(auth_url,config['oauth']['id'],config['oauth']['secret'])

# make issue
def make_issue(data,token=False):
    if not data['onto-repo'] in db.get_repo_info():
        return "Can't create issue for unknown repo"+r.content, 500
    if 'category-name' in data:
        data['categories'] = list(zip(data['category-name'],data['category-desc']))
    if not token:
        token = ah.installationToken(db.get_installation(data['onto-repo']))
        print(token)
    url = 'https://api.github.com/repos/{repo}/issues?access_token={token}'.format(repo=data['onto-repo'],token=token)
    title = ""
    if data["subtype"]=="new":
        title = "Create: "+data['trait-name']
    elif data["subtype"]=="update":
        title = "Update: "+data["update-search-selected"]
    elif data["subtype"]=="synonym":
        title = "Synonym for: "+data["synonym-search-selected"]
    issue = {'title': title,
             'body': render_template('issue.md.j2', data=data)}
    print(url,issue)
    r = requests.session().post(url,json=issue)
    if r.status_code == 201:
        print('Success')
        assign_and_label_issue(json.loads(r.content),data)
        return r.content, 201
    else:
        print('Could not create Issue')
        print('Response:', r.content)
        return 'Could not create Issue\nResponse:'+r.content, 500

# assign labels and assignees
def assign_and_label_issue(issue_obj,data):
    token = ah.installationToken(db.get_installation(data['onto-repo']))
    url = issue_obj["url"]+'?access_token={token}'.format(token=token)
    assignees = db.get_repo_info(repo=data['onto-repo'])["curators"]
    labels = []
    if data["subtype"]=="new":
        labels.append("Creation Request")
    elif data["subtype"]=="update":
        labels.append("Update Request")
    elif data["subtype"]=="synonym":
        labels.append("Synonym Request")
    
    r = requests.session().patch(url,json={
        "labels":labels,
        "assignees":assignees
    })
    
    if r.status_code == 200:
        print('Success')
    else:
        print('Could not label Issue')
        print('Response:', r.content)
        return 'Could not create Label\nResponse:'+r.content, 500
    
def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response
        
    return update_wrapper(no_cache, view)

@app.route('/')
@app.route('/index.html')
def root():
    return render_template('form.html.j2', repos=db.get_repo_info())
    
@app.route('/static/<path:path>')
def send_js(path):
    return send_from_directory('static', path)
    
@app.route('/variables', methods=["GET"])
def variables():
    repo = request.args.get('repo')
    if not db.get_repo_info(repo=repo):
        return "Can't get variables for unknown repo "+repo, 500
    variable_list = db.get_variables(repo)
    return jsonify(variable_list);

@app.route('/submit/email', methods=["POST"])
def new_issue_email():
    data = request.json
    if not data:
        return "must be json request", 400
    return make_issue(data);
    
@app.route('/submit/github', methods=["POST"])
def github_redirect():
    data = request.json
    data["email"] = ""
    if not data:
        return "must be json request", 400
    redirect_uri = oh.get_redirect({"goto":"issue","cached_as":db.cache_store(data)})
    return jsonify({"html_url":redirect_uri})
    
@app.route('/deploy')
def deploy():
    install_id = request.args.get('installation_id');
    return render_template('deploy.html.j2', repos=db.get_repo_info(install_id=install_id))

@app.route('/deploy/save', methods=["POST"])
def deploy_save():
    data = request.json
    updated = jsonify(db.set_repo_info(data['repo'],data))
    get_latest_releases([data['repo']])
    return updated
    
@app.route(oauth_path, methods=["GET"])
def oauth_receive():
    code = request.args.get('code')
    state = request.args.get('state')
    token = oh.get_token(state,code)
    state_content = oh.get_state(state)
    if state_content["goto"]=="issue":
        data = db.cache_retrieve(state_content["cached_as"])
        issue_data, responsecode = make_issue(data,token)
        issue_url = json.loads(issue_data)["html_url"]
        return redirect(issue_url,303)
    
@app.route('/webhook', methods=["POST"])
def webhook():
    data = request.json
    if not data:
        return "must be json request", 400
        
    if "release" in data and data['action']=="published":
        obo_path = dowload_obo(data['repository']['full_name'],data['release']['zipball_url'])
        return "release parsed", 202
        
    if "installation" in data and data['action']=="created":
        return create_installation(data)
        
    if "installation" in data and data['action']=="deleted":
        return delete_installation(data)
        
    if "installation" in data and data['action'] in ["added","removed"]:
        return update_installation(data)
        
def create_installation(data):
    install_id = data['installation']['id']
    add = [r['full_name'] for r in data['repositories']]
    db.add_repos(install_id,add)
    get_latest_releases(add)
    return " ".join(add)+" | added as "+str(install_id), 202

def delete_installation(data):
    install_id = data['installation']['id']
    remmed = db.rem_installation(install_id)
    msg = " ".join(r[0] for r in remmed)+" | removed as "+str(install_id)
    return msg, 202

def update_installation(data):
    install_id = data['installation']['id']
    rem = [r['full_name'] for r in data['repositories_removed']]
    add = [r['full_name'] for r in data['repositories_added']]
    db.add_repos(install_id,add)
    db.rem_repos(rem)
    get_latest_releases(add)
    return "updated "+str(install_id), 202
    
def get_latest_releases(repos):
    for repo in repos:
        token = ah.installationToken(db.get_installation(repo))
        release_info = "https://api.github.com/repos/{repo}/releases/latest?access_token={token}".format(repo=repo,token=token)
        info = requests.session().get(release_info).json()
        if not 'zipball_url' in info:
            print("No release for {repo}".format(repo=repo))
        else:
            dowload_obo(repo,info['zipball_url'])
                
    
def dowload_obo(repo,zipball_url):
    print("Downloading release for {repo}:".format(repo=repo),zipball_url)
    token = ah.installationToken(db.get_installation(repo))
    obopath = Path(db.get_repo_info(repo=repo)['master_obo_path'])
    download = zipball_url+"?access_token={token}".format(token=token)
    r = requests.session().get(download)
    with zipfile.ZipFile(io.BytesIO(r.content)) as zp:
        obos = [f for f in zp.namelist() if obopath==Path(f).relative_to(f.split(os.path.sep)[0])]
        obos.sort()
        if(len(obos)>0):
            master_obo = obos[0]
            with io.TextIOWrapper(zp.open(master_obo), encoding="utf-8") as to_parse:
                db.parse_and_update(repo,to_parse)
