#!/usr/bin/python

from flup.server.fcgi import WSGIServer
from ledslie.site import app

if __name__ == '__main__':
    WSGIServer(app, bindAddress="/var/run/ledslie/ledslie.sock").run()
