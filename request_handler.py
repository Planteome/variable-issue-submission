from flask import Flask, request, send_from_directory
from jinja2 import Environment, FunctionLoader
import json
import requests


# file loader
def load(name):
    with open(name) as fi:
        return fi.read()

# config
token = load("token.txt").strip()
        
# request template
env = Environment(loader=FunctionLoader(load),trim_blocks=True);
issue_template = env.get_template('issue_template.md')
issue_url = 'https://api.github.com/repos/{repo}/issues?access_token={token}'

# make issue
def make_issue(data):
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

@app.route('/')
@app.route('/index.html')
def root():
    return send_from_directory('','index.html')
    
@app.route('/static/<path:path>')
def send_js(path):
    return send_from_directory('static', path)
    
@app.route('/newIssue', methods=["POST"])
def new_issue():
    if not request.json:
        abort(400)
    data = request.json
    with open("submission_log.txt","a") as log:
        log.write(json.dumps(data)+"\n")
    if 'category-name' in data:
        data['categories'] = list(zip(data['category-name'],data['category-desc']))
    make_issue(data)
    return "success"
