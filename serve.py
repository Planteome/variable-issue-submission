from gevent.wsgi import WSGIServer
from request_handler import app

http_server = WSGIServer(('', 5000), app)
http_server.serve_forever()
