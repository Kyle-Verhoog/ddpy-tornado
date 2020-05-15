# ddtrace tornado app

A Tornado app to experiment with tracing.

## the app

The app provides different routes for testing various tracer functionalities.


```bash

```


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
$ DATADOG_PATCH_MODULES="tornado:true,sqlalchemy:true,psycopg:true" ddtrace-run python app.py
```


## migrations

### run migrations

```bash
$ alembic upgrade head
```

### creating a new migration
```bash
# create new migration
$ alembic revision --autogenerate -m "my change here"
```
