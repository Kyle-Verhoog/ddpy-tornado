# ddtrace tornado app

A Tornado app to experiment with tracing.

## setup

```bash

# start up the database and app
$ docker-compose up -d

# or manually..

# in your virtualenv (create with virtualenv --python=python3 .venv)
source .venv/bin/activate
pip install -r requirements.txt

# run migrations
$ alembic upgrade head

# start the app
$ python app.py
```


## migrations

```bash
# create new migration
$ alembic revision --autogenerate -m "my change here"
$ alembic upgrade head
```
