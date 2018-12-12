from gevent.wsgi import WSGIServer
import werkzeug.serving
from request_handler import app
import json

with open("config.json") as conf_file:
    config = json.load(conf_file)

@werkzeug.serving.run_with_reloader
def runServer():
    app.debug = True
    http_server = WSGIServer(('', config['port']), app)
    http_server.serve_forever()
runServer()
