import os
import psycopg
from dotenv import load_dotenv

load_dotenv()


def conectar():
    return psycopg.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "SIMPA"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD"),
        sslmode=os.getenv("PGSSLMODE", "prefer")
    )