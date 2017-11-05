#!/usr/bin/python

from flup.server.fcgi import WSGIServer
from ledslie.interface.site import make_app

if __name__ == '__main__':
    site_app = make_app()
    WSGIServer(site_app, bindAddress="/var/run/ledslie/ledslie.sock").run()
