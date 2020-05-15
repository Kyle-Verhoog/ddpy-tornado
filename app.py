try:
    from ddtrace import patch, tracer

    patch(tornado=True, sqlalchemy=True, psycopg=True)
except ImportError:

    class Span(object):
        def __enter__(self):
            pass

        def __exit__(self, *args, **kwargs):
            pass

    class Tracer(object):
        def wrap(self):
            def wrapped(f):
                return f

            return wrapped

        def trace(self, *args, **kwargs):
            return Span()

    tracer = Tracer()

import logging
import os

import sqlalchemy
import tornado.ioloop
import tornado.options
import tornado.web
from tornado import gen
from tornado.httpclient import AsyncHTTPClient
from vendor.tornado_sqlalchemy import SessionMixin, SQLAlchemy, as_future


logging.basicConfig()
log = logging.getLogger(__name__)



PORT = os.getenv("PORT", 8888)
DB_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres"
)


db = SQLAlchemy(url=DB_URL)


class User(db.Model):
    __tablename__ = "users"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String)


class MainHandler(SessionMixin, tornado.web.RequestHandler):
    @gen.coroutine
    def get(self):
        count_fut = as_future(self.session.query(User).count)
        http_client = AsyncHTTPClient()
        yield self.work()
        count = yield count_fut
        self.render("template.html", count=count)

    @tracer.wrap()
    @gen.coroutine
    def work(self):
        yield gen.sleep(0.005)


class StressHandler(tornado.web.RequestHandler):
    @gen.coroutine
    def get(self):
        num_traces = int(self.get_argument("traces", 1))
        num_spans_per_trace = int(self.get_argument("spans_per_trace", 1))
        num_str_tags_per_span = int(self.get_argument("str_tags_per_span", 5))
        num_int_tags_per_span = int(self.get_argument("int_tags_per_span", 5))
        tag_key_size = int(self.get_argument("tag_key_size", 10))
        str_tag_value_size = int(self.get_argument("tag_value_size", 15))

        log.warning("handling request with num_traces=%d, num_spans_per_trace=%d", num_traces, num_spans_per_trace)

        def _set_tags(span):
            for i in range(num_str_tags_per_span):
                span.set_tag("s{}".format(str(i) * (tag_key_size-1)), "*" * str_tag_value_size)

            for i in range(num_int_tags_per_span):
                span.set_tag("i{}".format(str(i) * (tag_key_size-1)), 12312312)

        for _ in range(num_traces):
            with tracer.trace("operation", service="stresser", resource="GET /stress") as s:
                _set_tags(s)
                for i in range(num_spans_per_trace-1):
                    with tracer.trace("child_operation_{}".format(i)) as s:
                        _set_tags(s)

        self.write("OK")


class DatabaseStressHandler(SessionMixin, tornado.web.RequestHandler):
    @gen.coroutine
    def get(self):
        num_requests = int(self.get_argument("num_db_requests", 10))
        log.warning("handling request with %d db requests", num_requests)

        for _ in range(num_requests):
            count_fut = as_future(self.session.query(User).count)
            count = yield count_fut

        self.render("template.html", count=count)



def make_app():
    tornado.options.parse_command_line()
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/stress", StressHandler),
        (r"/db_stress", DatabaseStressHandler),
        ], db=db,)


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
