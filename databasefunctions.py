import sqlite3
import json
import pyobo
from threading import Timer

_DBPATH = "./varsub.db"

def __main():
    with sqlite3.connect(_DBPATH) as conn:
        c = conn.cursor()
        if not c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='repositories';").fetchone():
            c.execute('''CREATE TABLE repositories (
                             repo TEXT PRIMARY KEY,
                             install_id TEXT NOT NULL,
                             name TEXT NOT NULL,
                             curators TEXT NOT NULL,
                             master_obo_path TEXT NOT NULL,
                             variables_json TEXT NOT NULL
                         );''')
        if not c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='datacache';").fetchone():
            c.execute('''CREATE TABLE datacache (
                             cache_id INTEGER PRIMARY KEY AUTOINCREMENT,
                             json TEXT NOT NULL
                         );''')

def update_variables(repo,search_data):
    with sqlite3.connect(_DBPATH) as conn:
        c = conn.cursor()
        search_json = json.dumps(search_data)
        c.execute("UPDATE repositories SET variables_json = ? WHERE repo=?;", [
            search_json,
            repo
        ]);
    
def parse_and_update(repo,obo):
    search_data = []
    o = pyobo(obo)
    for term in o.getTerms():
#        if any(relationship.value.relation.id == "variable_of" for relationship in term["relationship"]):
            #is a variable
         search_data.append({
             "id":term["id"].value.id,
             "name":term["name"].value,
             "def":term["def"].value if "def" in term else "",
              "synonyms":", ".join([syn.value for syn in term["synonym"]]),
         })
         
    update_variables(repo, search_data)
    
def get_variables(repo):
    with sqlite3.connect(_DBPATH) as conn:
        c = conn.cursor()
        c.execute("SELECT variables_json FROM repositories WHERE repo=?", [repo])
        return json.loads(c.fetchone()[0])
    
def add_repos(install_id,repos):
    with sqlite3.connect(_DBPATH) as conn:
        c = conn.cursor()
        for repo in repos:
            c.execute("DELETE FROM repositories WHERE repo=?;", [repo])
            c.execute("INSERT INTO repositories VALUES (?,?,?,?,?,?);", [
                repo,
                install_id,
                repo,
                "[]",
                "master.obo",
                "[]"
                ])

def rem_repos(repos):
    with sqlite3.connect(_DBPATH) as conn:
        c = conn.cursor()
        for repo in repos:
            c.execute("DELETE FROM repositories WHERE repo=?;", [repo])
            
def rem_installation(install_id):
    with sqlite3.connect(_DBPATH) as conn:
        c = conn.cursor()
        c.execute('SELECT repo FROM repositories WHERE install_id=?;', [install_id])
        targets = c.fetchall()
        c.execute("DELETE FROM repositories WHERE install_id=?;", [install_id])
        return targets
            
def get_installation(repo):
    with sqlite3.connect(_DBPATH) as conn:
        c = conn.cursor()
        c.execute("SELECT install_id FROM repositories WHERE repo=?;", [repo])
        return c.fetchone()[0]
        
def get_repo_info(install_id=None,repo=None):
    result = {}
    with sqlite3.connect(_DBPATH) as conn:
        c = conn.cursor()
        if(install_id!=None):
            c.execute("SELECT * FROM repositories WHERE install_id=?;", [install_id])
        elif(repo!=None):
            c.execute("SELECT * FROM repositories WHERE repo=?;", [repo])
        else:
            c.execute("SELECT * FROM repositories;")
        for row in c.fetchall():
            result[row[0]] = {
                "name": row[2],
                "curators": json.loads(row[3]),
                "master_obo_path": row[4]
            }
    if(repo!=None): result = result[repo]
    return result

def set_repo_info(repo,info):
    with sqlite3.connect(_DBPATH) as conn:
        c = conn.cursor()
        c.execute("UPDATE repositories SET name = ?, curators = ?, master_obo_path = ? WHERE repo=?;", [
            info['name'],
            json.dumps(info['curators']),
            info['master_obo_path'],
            repo
        ]);
    return get_repo_info(repo=repo);
        
    
def cache_store(data, timeout=14400):
    json_data = json.dumps(data)
    with sqlite3.connect(_DBPATH) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO datacache(json) VALUES (?);", [json_data])
        c.execute("SELECT cache_id FROM datacache WHERE rowid=last_insert_rowid();")
        cache_id = c.fetchone()[0]
    Timer(timeout, cache_retrieve, (cache_id,) ).start()
    return cache_id

def cache_retrieve(cache_id):
    with sqlite3.connect(_DBPATH) as conn:
        c = conn.cursor()
        c.execute('SELECT json FROM datacache WHERE cache_id=?;', [cache_id])
        cached_data = c.fetchone()[0]
        c.execute('DELETE FROM datacache WHERE cache_id=?;', [cache_id])
        return json.loads(cached_data)
     
__main()
