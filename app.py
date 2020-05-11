try:
    from ddtrace import patch, tracer

    patch(tornado=True, sqlalchemy=True, psycopg=True)
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

import sqlalchemy
import tornado.ioloop
import tornado.web
from tornado import gen
from tornado.httpclient import AsyncHTTPClient
from tornado_sqlalchemy import SessionMixin, SQLAlchemy, as_future


PORT = os.getenv("PORT", 8888)
DB_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres"
)


db = SQLAlchemy(DB_URL)


class User(db.Model):
    __tablename__ = "users"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String)


# engine = sqlalchemy.create_engine(DB_URL)
# Base.metadata.create_all(engine)
# Session = sessionmaker(bind=engine)


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


def make_app():
    return tornado.web.Application([(r"/", MainHandler),], db=db,)


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
