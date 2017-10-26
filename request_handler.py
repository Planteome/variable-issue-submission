from flask import Flask, request, send_from_directory, make_response
from jinja2 import Environment, FunctionLoader
from flask_basicauth import BasicAuth
from functools import wraps, update_wrapper
from datetime import datetime
import json
import requests


# file loader
def load(name):
    with open(name) as fi:
        return fi.read()
        
# request and log templates
env = Environment(loader=FunctionLoader(load),trim_blocks=True);
issue_template = env.get_template('issue_template.md')
log_template = env.get_template('log_template.txt')
issue_url = 'https://api.github.com/repos/{repo}/issues?access_token={token}'

# make issue
def make_issue(data):
    with open("submission_log.txt","a") as log:
        log.write(log_template.render(data=data))
    url = issue_url.format(repo=data['crop-repo'],token=token)
    issue = {'title': data['trait-name'],
             'body': issue_template.render(data=data),
             'labels': ["Variable Request"]}
    r = requests.session().post(url,json=issue)
    if r.status_code == 201:
        print('Success')
    else:
        print('Could not create Issue')
        print('Response:', r.content)

# app setup
app = Flask(__name__,static_url_path='')
# config
token =""
with open("config.json") as conf_file:
    config = json.load(conf_file);
    token = config['token']
    app.config['BASIC_AUTH_USERNAME'] = config['username']
    app.config['BASIC_AUTH_PASSWORD'] = config['password']
basic_auth = BasicAuth(app)

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
    return send_from_directory('','index.html')
    
@app.route('/log')
@app.route('/log.txt')
@basic_auth.required
@nocache
def log_file():
    return send_from_directory('','submission_log.txt')
    
@app.route('/static/<path:path>')
def send_js(path):
    return send_from_directory('static', path)
    
@app.route('/newIssue', methods=["POST"])
def new_issue():
    if not request.json:
        abort(400)
    data = request.json
    if 'category-name' in data:
        data['categories'] = list(zip(data['category-name'],data['category-desc']))
    make_issue(data)
    return "success"
