from flask import Flask, request, send_from_directory, make_response, redirect, render_template, jsonify
from jinja2 import Environment, FunctionLoader
from flask_basicauth import BasicAuth
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
from threading import Timer

# file loader
def load(name):
    with open(name) as fi:
        return fi.read()
        
# app setup
app = Flask(__name__)

# config
with open("config.json") as conf_file:
    config = json.load(conf_file);
app.config['BASIC_AUTH_USERNAME'] = config['username']
app.config['BASIC_AUTH_PASSWORD'] = config['password']
basic_auth = BasicAuth(app)
pkey = Path(config['skey']).read_text()

ah = GHAppAuthHandler(config['iss'], pkey)
oh = GHOAuthHandler(urllib.parse.urljoin(config['base_url'], "/submit/github/authorized"),config['oauth']['id'],config['oauth']['secret'])

# make issue
def make_issue(data,token=False):
    if not data['onto-repo'] in config['repo_info']:
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

def assign_and_label_issue(issue_obj,data):
    token = ah.installationToken(db.get_installation(data['onto-repo']))
    url = issue_obj["url"]+'?access_token={token}'.format(token=token)
    assignees = config['repo_info'][data['onto-repo']]["curators"]
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
    return render_template('form.html.j2', repos=config["repo_info"])
    return send_from_directory('','index.html')
    
@app.route('/static/<path:path>')
def send_js(path):
    return send_from_directory('static', path)
    
@app.route('/variables', methods=["GET"])
def variables():
    repo = request.args.get('repo')
    if not repo in config['repo_info']:
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
    if not data:
        return "must be json request", 400
    redirect_uri = oh.get_redirect({"cached_as":cache_val(data)})
    return jsonify({"html_url":redirect_uri})
    
@app.route('/submit/github/authorized', methods=["GET"])
def new_issue_github():
    code = request.args.get('code')
    state = request.args.get('state')
    token = oh.get_token(state,code)
    data = uncache_val(oh.get_state(state)["cached_as"])
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
        
def create_installation(data):
    install_id = data['installation']['id']
    repos = [r['full_name'] for r in data['repositories']]
    db.add_installation(install_id,repos)
    return " ".join(repos)+" | added as "+str(install_id), 202

def delete_installation(data):
    install_id = data['installation']['id']
    remmed = db.rem_installation(install_id)
    msg = " ".join(r[0] for r in remmed)+" | removed as "+str(install_id)
    return msg, 202

def dowload_obo(repo,zipball_url):
    print(repo,zipball_url)
    token = ah.installationToken(db.get_installation(repo))
    download = zipball_url+"?access_token={token}".format(token=token)
    r = requests.session().get(download)
    with zipfile.ZipFile(io.BytesIO(r.content)) as zp:
        obos = [f for f in zp.namelist() if f.endswith(".obo")]
        obos.sort()
        default_obo = obos[1]
        with io.TextIOWrapper(zp.open(default_obo)) as to_parse:
            db.parse_and_update(repo,to_parse)

vcache = {}
vcid = 0
def cache_val(val):
    global vcid
    global vcache
    print(vcache)
    vcache[vcid] = val
    Timer(14400, uncache_val, (vcid,) ).start()
    vcid+=1
    return vcid-1
def uncache_val(vcid):
    global vcache
    print(vcache)
    val = vcache[vcid]
    del vcache[vcid]
    return val
