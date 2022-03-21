#!/usr/bin/env python

import os
import sys
import logging
import json
import time
import asyncio

import tornado.httpserver
import tornado.ioloop
import tornado.wsgi
import tornado.web
from urllib.parse import urlparse
from tornado.options import define, options, parse_command_line

import tornado.iostream
import tornado.httpclient
import tornado.httputil
import asyncssh

from client_info import get_stats_data

class APIhandler(tornado.web.RequestHandler):
    async def get_server_status(self, hostname, username, port):
        async with asyncssh.connect(hostname, username=username, port=port) as conn:
            data = await get_stats_data(conn)
        data['name'] = hostname
        data['type'] = 'KVM'
        data['custom'] = ""
        data['location'] = 'US'
        data['host'] = None
        data['online4'] = True
        data['online6'] = True
        return data

    async def get(self):
        hostname = '10.208.63.54'
        username = 'huangjunjie'
        port = 22
        servers = [
            ('10.208.63.54', 'huangjunjie', 22),
            ('91.200.242.105', 'h12345jack', 22),
        ]
        datas  = []
        for server in servers:
            hostname, username, port = server
            datas.append(
                self.get_server_status(hostname, username, port)
            )       
        datas = await asyncio.gather(*datas)
        res = {
            'servers': datas,
            'updated': f'{int(time.time())}'
        }
        self.write(res)


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")


class MainHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('templates/web/index.html')
        
class LoginHandler(BaseHandler):
    def get(self):
        self.write('<html><body><form action="/login" method="post">'
                   'Username: <input type="text" name="name">'
                   'Password: <input type="password" name="password">'
                   '<input type="submit" value="Sign in">'
                   '</form></body></html>')

    def post(self):
        username = self.get_argument("name")
        password = self.get_argument("password")
        if username == 'admin' and password == 'admin':
            self.set_secure_cookie("user", username)
        self.redirect("/")

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_all_cookies()
        self.redirect("/")



class ServerStatusApplication(tornado.web.Application):
    conns = {}

    def __init__(self, url_patterns,  **kwags):


        tornado.web.Application.__init__(self, url_patterns, **kwags)


if __name__ == "__main__":
    # path to your settings module
    define("port", default=18888, help="run on the given port", type=int)
    define("config", default=None, help="tornado config file")
    define("debug", default=False, help="debug mode")
    define("ssh_connected_timeout", default=5.0, help="ssh connected timeout, default: 5.0")

    tornado_app = ServerStatusApplication(
        [
            (r'/ss_static/(.*)', tornado.web.StaticFileHandler, {"path": './templates/web'}),
            (r'/json/.*', APIhandler),
            (r"/login", LoginHandler),
            (r'/logout', LogoutHandler),
            (r'.*', MainHandler),
        ],
        debug=options.debug,
        autoreload=options.debug,
        login_url='/login',
        cookie_secret="Bj0aRCDg8fPyCNsA9Aub8i32U"
    )
    parse_command_line()
    if options.debug:
        tornado.log.enable_pretty_logging()
    print(f'Runining on: http://localhost:{options.port}')
    tornado_app.listen(options.port, address='0')
    tornado.ioloop.IOLoop.current().start()
