import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL, make_url

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

backend = os.getenv("NETPULSE_BACKEND", "memory")
if backend not in {"memory", "mysql"}:
    raise ValueError("NETPULSE_BACKEND must be memory or mysql")


def database_url() -> URL:
    if value := os.getenv("DATABASE_URL"):
        return make_url(value)
    return URL.create(
        "mysql+pymysql",
        username=os.getenv("MYSQL_USER", "netpulse_user"),
        password=os.getenv("MYSQL_PASSWORD"),
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        database=os.getenv("MYSQL_DB", "netpulse_db"),
    )
