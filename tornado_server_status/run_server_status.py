#!/usr/bin/env python
import os
import time
import logging
import pkgutil

import asyncio
from collections import defaultdict

import tornado.ioloop
import tornado.web
from tornado.options import define, options
from tornado.options import parse_command_line, parse_config_file

import asyncssh
import traceback

from .client_info import get_stats_data

import tornado.ioloop
import tornado.web

from pkg_resources import resource_string


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class APIhandler(tornado.web.RequestHandler):

    async def get_server_status(self, host, first_query=None):
        data = {}
        data['name'] = host
        data['type'] = 'Unkown'
        data['custom'] = ""
        data['location'] = 'Unkown'
        data['host'] = None
        data['online4'] = False
        data['online6'] = False
        data.update(self.application.first_query_results[host])
        try:
            conn = self.application.conns.get(host)
            if not conn is None:
                return_data = await asyncio.wait_for(
                    get_stats_data(conn, first_query=first_query),
                    timeout=options.ssh_query_timeout
                )
                data['online4'] = True
                data['online6'] = True
                data.update(return_data)
        except Exception as e:
            if options.debug:
                traceback.print_exc()
                logging.exception(e)
        return data

    async def get(self):
        # 尝试建立链接，如果有链接，则直接返回链接，否则
        # idea from https://github.com/ronf/asyncssh/issues/270
        servers = self.application.servers
        tasks = []
        for server in servers:
            host, username, port, password = '127.0.0.1', 'root', '22', None
            try:
                if len(server) == 1:
                    host = server
                elif len(server) == 2:
                    host, username = server
                elif len(server) == 3:
                    host, username, port = server
                elif len(server) == 4:
                    host, username, port, password = server
                conn = self.application.conns.get(host)
                if not conn:
                    last_failed_t = self.application.failed_hosts[host]
                    now = time.time()
                    interval = (now - last_failed_t)
                    if interval > options.ssh_connected_retry_interval:
                        conn = await asyncio.wait_for(
                            asyncssh.connect(
                                host=host, username=username, port=port,
                                password=password, known_hosts=None
                            ),
                            timeout=options.ssh_connected_timeout
                        )
                        self.application.conns[host] = conn
                        first_query_res = await self.get_server_status(
                                            host, first_query=True
                                        )
                        assert first_query_res['online4']
                        if first_query_res['online4']:
                            self.application.first_query_results[host] = first_query_res
                            print(host, 'connected!')
            except Exception as e:
                self.application.failed_hosts[host] = time.time()
                if options.debug:
                    logging.exception(e)

            tasks.append(
                self.get_server_status(host)
            )

        datas = await asyncio.gather(*tasks)
        res = {
            'servers': datas,
            'updated': f'{int(time.time())}'
        }
        self.write(res)


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        if options.password is None:
            return True
        return self.get_secure_cookie("user")


class MainHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        html_path = os.path.join(BASE_DIR, 'templates/web/index.html')
        self.render(html_path)


class LoginHandler(BaseHandler):

    def get(self):
        error_message = ""
        html_path = os.path.join(BASE_DIR, 'templates/web/login.html')
        self.render(html_path, error_message=error_message)

    def post(self):
        error_message = "Wrong name or password"
        username = self.get_argument("name", "")
        password = self.get_argument("password", "")
        if username == options.username and password == options.password:
            self.set_secure_cookie("user", username)
            self.redirect('/')
        else:
            html_path = os.path.join(BASE_DIR, 'templates/web/login.html')
            self.render(html_path, error_message=error_message)


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_all_cookies()
        self.redirect("/")


class ServerStatusApplication(tornado.web.Application):
    conns = defaultdict(lambda: None)
    failed_hosts = defaultdict(int)
    severs = []
    first_query_results = defaultdict(dict)

    def __init__(self, url_patterns,  **kwags):
        self.servers = options.servers
        tornado.web.Application.__init__(self, url_patterns, **kwags)


def main():
    # path to your settings module
    define("port", default=21388, help="run on the given port", type=int)
    define("config", default=None, help="tornado config file")
    define("debug", default=False, help="debug mode")
    define("servers", default=[('127.0.0.1', 'root', 22)], help="ssh connected timeout, default: 5.0")
    define("ssh_connected_timeout", default=5.0, help="ssh connect timeout, default: 5.0")
    define("ssh_connected_retry_interval", default=60.0, help="ssh connect retry interval, default: 60.0")
    define("ssh_query_timeout", default=5.0, help="ssh query timeout, default: 5.0")
    define("username", default=None, help="username")
    define("password", default=None, help="password")


    parse_command_line()
    if options.config:
        parse_config_file(options.config)
    if options.debug:
        tornado.log.enable_pretty_logging()

    static_dir = os.path.join(BASE_DIR, './templates/web')

    tornado_app = ServerStatusApplication(
        [
            (r'/ss_static/(.*)', tornado.web.StaticFileHandler, {"path": static_dir}),
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

    print(f'Runining on: http://localhost:{options.port}')
    tornado_app.listen(options.port, address='0')
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()
