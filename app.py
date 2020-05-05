try:
    from ddtrace import patch, tracer

    patch(tornado=True)
except ImportError:

    class Span(object):
        def __enter__(self):
            pass

        def __exit__(*args, **kwargs):
            pass

    class Tracer(object):
        def wrap(self):
            def wrapped(f):
                return f

            return wrapped

        def trace(self, *args, **kwargs):
            return Span()

    tracer = Tracer()

import os

import tornado.ioloop
import tornado.web
from tornado import gen
from tornado.httpclient import AsyncHTTPClient


PORT = os.getenv("PORT", 8888)


class MainHandler(tornado.web.RequestHandler):
    @gen.coroutine
    def get(self):
        http_client = AsyncHTTPClient()
        yield self.work()
        self.render("template.html")

    @tracer.wrap()
    @gen.coroutine
    def work(self):
        yield gen.sleep(0.005)


class SuccessHandler(tornado.web.RequestHandler):
    @gen.coroutine
    def get(self):
        self.write("hi")


class FailureHandler(tornado.web.RequestHandler):
    @gen.coroutine
    def get(self):
        raise Exception("Error")


def make_app():
    return tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/success", SuccessHandler),
            (r"/failure", FailureHandler),
        ]
    )


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
