import os


class Config:

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "careermatch-development-secret-key"
    )

    DB_HOST = os.environ.get(
        "DB_HOST",
        "localhost"
    )

    DB_PORT = os.environ.get(
        "DB_PORT",
        "5432"
    )

    DB_NAME = os.environ.get(
        "DB_NAME",
        "careermatch"
    )

    DB_USER = os.environ.get(
        "DB_USER",
        "postgres"
    )

    DB_PASSWORD = os.environ.get(
        "DB_PASSWORD",
        "omkar@22"
    )