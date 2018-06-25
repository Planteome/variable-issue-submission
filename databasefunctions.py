import sqlite3
import json
import pyobo
from threading import Timer

_DBPATH = "./varsub.db"

def __main():
    with sqlite3.connect(_DBPATH) as conn:
        c = conn.cursor()
        if not c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='variables';").fetchone():
            c.execute('''CREATE TABLE variables (
                             repo TEXT PRIMARY KEY,
                             json TEXT NOT NULL
                         );''')
        if not c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='installations';").fetchone():
            c.execute('''CREATE TABLE installations (
                             repo TEXT PRIMARY KEY,
                             install_id TEXT NOT NULL
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
        c.execute("DELETE FROM variables WHERE repo=?", [repo])
        c.execute("INSERT INTO variables VALUES (?,?)", [
            repo,
            search_json
            ])
    
def parse_and_update(repo,obo):
    search_data = []
    o = pyobo(obo)
    print(type(o["CO_331:0000149"]),o["CO_331:0000149"]["relationship"])
    for term in o.getTerms():
        if any(relationship.value.relation.id == "variable_of" for relationship in term["relationship"]):
            #is a variable
            search_data.append({
                "id":term["id"].value.id,
                "name":term["name"].value,
                "def":term["def"].value if "def" in term else "",
                "synonyms":", ".join([syn.value for syn in term["synonym"]]),
            })
            if term['id'].value.id=="CO_331:0000149":
                print(term,search_data[-1])
            
    update_variables(repo, search_data)
    
def get_variables(repo):
    with sqlite3.connect(_DBPATH) as conn:
        c = conn.cursor()
        c.execute("SELECT json FROM variables WHERE repo=?", [repo])
        return json.loads(c.fetchone()[0])
    
def add_installation(install_id,repos):
    with sqlite3.connect(_DBPATH) as conn:
        c = conn.cursor()
        for repo in repos:
            c.execute("DELETE FROM installations WHERE repo=?;", [repo])
            c.execute("INSERT INTO installations VALUES (?,?);", [
                repo,
                install_id ])
            
def rem_installation(install_id):
    with sqlite3.connect(_DBPATH) as conn:
        c = conn.cursor()
        c.execute('SELECT repo FROM installations WHERE install_id=?;', [install_id])
        targets = c.fetchall()
        c.execute("DELETE FROM installations WHERE install_id=?;", [install_id])
        return targets
            
def get_installation(repo):
    with sqlite3.connect(_DBPATH) as conn:
        c = conn.cursor()
        c.execute("SELECT install_id FROM installations WHERE repo=?;", [repo])
        return c.fetchone()[0]
    
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
