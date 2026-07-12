import os.path
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

SQLITE = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
        "OPTIONS": {
            "timeout": 120,
        },
    },
}

POSTGRESQL_FROM_PARTS = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", default=""),
        "USER": env("DB_USER", default=""),
        "PASSWORD": env("DB_PASSWORD", default=""),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="5432"),
        "ATOMIC_REQUESTS": True,
        "OPTIONS": {
            "options": f'-c search_path={env("DB_SCHEMA", default="public")}',
        },
    },
}

DATABASE_URL = env("DATABASE_URL", default="").strip()
if DATABASE_URL:
    database_config = env.db_url_config(DATABASE_URL)
    database_config["CONN_MAX_AGE"] = 600
    POSTGRESQL = {"default": database_config}
else:
    POSTGRESQL = POSTGRESQL_FROM_PARTS
