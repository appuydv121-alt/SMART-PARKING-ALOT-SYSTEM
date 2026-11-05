import re
import sqlite3
from pathlib import Path

from config.settings import (
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
    USE_MYSQL,
)

import os

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("SMART_PARKING_DB_PATH", str(ROOT / "smart_parking.db")))
SCHEMA_PATH = ROOT / "database" / "schema.sql"
MYSQL_SCHEMA_PATH = ROOT / "database" / "schema_mysql.sql"
TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")
REQUIRE_TURSO = os.getenv("SMART_PARKING_REQUIRE_TURSO", "false").lower() in {"1", "true", "yes"}


class _MySQLRow(dict):
    def __init__(self, row):
        super().__init__(row)
        self._values = list(row.values())

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return super().__getitem__(key)


class _MySQLCursor:
    def __init__(self, cursor):
        self._cursor = cursor

    def fetchone(self):
        row = self._cursor.fetchone()
        return _MySQLRow(row) if row is not None else None

    def fetchall(self):
        return [_MySQLRow(row) for row in self._cursor.fetchall()]

    @property
    def lastrowid(self):
        return self._cursor.lastrowid


class _MySQLConnection:
    def __init__(self, connection):
        self._connection = connection

    def execute(self, query, parameters=()):
        query = re.sub(r"\?", "%s", query)
        query = re.sub(
            r"INSERT\s+OR\s+IGNORE\s+INTO\b",
            "INSERT IGNORE INTO",
            query,
            flags=re.IGNORECASE,
        )
        query = re.sub(
            r"datetime\s*\(\s*'now'\s*\)",
            "CURRENT_TIMESTAMP",
            query,
            flags=re.IGNORECASE,
        )
        query = re.sub(
            r"date\s*\(\s*'now'\s*,\s*'-7 days'\s*\)",
            "DATE_SUB(CURRENT_DATE, INTERVAL 7 DAY)",
            query,
            flags=re.IGNORECASE,
        )
        query = re.sub(
            r"date\s*\(\s*'now'\s*,\s*'-30 days'\s*\)",
            "DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)",
            query,
            flags=re.IGNORECASE,
        )
        query = re.sub(
            r"date\s*\(\s*'now'\s*\)",
            "CURRENT_DATE",
            query,
            flags=re.IGNORECASE,
        )
        query = re.sub(
            r"date\s*\(\s*([A-Za-z_][\w.]*)\s*\)",
            r"DATE(\1)",
            query,
            flags=re.IGNORECASE,
        )
        cursor = self._connection.cursor(dictionary=True, buffered=True)
        cursor.execute(query, parameters)
        return _MySQLCursor(cursor)

    def commit(self):
        self._connection.commit()

    def close(self):
        self._connection.close()


def _mysql_connection():
    if not re.fullmatch(r"[A-Za-z0-9_]+", DB_NAME):
        raise RuntimeError("SMART_PARKING_DB_NAME may contain only letters, numbers, and underscores.")
    if not DB_PASSWORD:
        raise RuntimeError("Configure SMART_PARKING_DB_PASSWORD in your environment or .env file.")

    import mysql.connector

    connection_options = {
        "host": DB_HOST,
        "port": DB_PORT,
        "user": DB_USER,
        "password": DB_PASSWORD,
    }
    server_connection = mysql.connector.connect(**connection_options)
    try:
        cursor = server_connection.cursor()
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4"
        )
        server_connection.commit()
    finally:
        server_connection.close()

    return _MySQLConnection(
        mysql.connector.connect(database=DB_NAME, **connection_options)
    )


def get_connection():
    if bool(TURSO_DATABASE_URL) != bool(TURSO_AUTH_TOKEN):
        raise RuntimeError("Both TURSO_DATABASE_URL and TURSO_AUTH_TOKEN must be configured.")

    if TURSO_DATABASE_URL and TURSO_AUTH_TOKEN:
        import turso_serverless

        conn = turso_serverless.connect(TURSO_DATABASE_URL, auth_token=TURSO_AUTH_TOKEN)
        conn.row_factory = turso_serverless.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    if REQUIRE_TURSO:
        raise RuntimeError("Turso is required. Configure TURSO_DATABASE_URL and TURSO_AUTH_TOKEN.")

    if USE_MYSQL:
        return _mysql_connection()

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_database():
    conn = get_connection()
    if USE_MYSQL and not (TURSO_DATABASE_URL and TURSO_AUTH_TOKEN):
        sql = MYSQL_SCHEMA_PATH.read_text(encoding="utf-8")
        for statement in sql.split(";"):
            if statement.strip():
                conn.execute(statement)

        user_columns = {
            row["COLUMN_NAME"]
            for row in conn.execute(
                "SELECT COLUMN_NAME FROM information_schema.columns "
                "WHERE table_schema = DATABASE() AND table_name = 'users'"
            ).fetchall()
        }
        if "plain_password" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN plain_password VARCHAR(255)")
        if "created_by" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN created_by INT")
    else:
        sql = SCHEMA_PATH.read_text(encoding="utf-8")
        for statement in sql.split(";"):
            if statement.strip():
                conn.execute(statement)

        user_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()
        }
        if "plain_password" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN plain_password TEXT")
        if "created_by" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN created_by INTEGER")

    conn.execute(
        "UPDATE users SET plain_password = 'admin123' "
        "WHERE username = 'admin' AND (plain_password IS NULL OR plain_password = '')"
    )

    conn.commit()
    conn.close()


def initialize_database():
    if USE_MYSQL and not (TURSO_DATABASE_URL or REQUIRE_TURSO):
        raise RuntimeError("Refusing to reset a MySQL database.")
    if TURSO_DATABASE_URL or REQUIRE_TURSO:
        raise RuntimeError("Refusing to reset a remote or required Turso database.")

    conn = get_connection()
    drop_sql = """
    DROP TABLE IF EXISTS receipts;
    DROP TABLE IF EXISTS payments;
    DROP TABLE IF EXISTS parking_records;
    DROP TABLE IF EXISTS parking_rates;
    DROP TABLE IF EXISTS vehicles;
    DROP TABLE IF EXISTS parking_slots;
    DROP TABLE IF EXISTS parking_lots;
    DROP TABLE IF EXISTS users;
    """
    conn.executescript(drop_sql)
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()
    conn.close()
