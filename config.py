import os


class Config:

    # ------------------------------------------------------------
    # FLASK SECRET KEY
    # ------------------------------------------------------------

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "careermatch-development-secret-key"
    )

    # ------------------------------------------------------------
    # NEON / POSTGRESQL DATABASE URL
    # ------------------------------------------------------------

    DATABASE_URL = os.environ.get("DATABASE_URL")

    # ------------------------------------------------------------
    # LOCAL POSTGRESQL SETTINGS
    # Used when DATABASE_URL is not available
    # ------------------------------------------------------------

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