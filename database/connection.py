import sqlite3
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("SMART_PARKING_DB_PATH", str(ROOT / "smart_parking.db")))
SCHEMA_PATH = ROOT / "database" / "schema.sql"
TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")
REQUIRE_TURSO = os.getenv("SMART_PARKING_REQUIRE_TURSO", "false").lower() in {"1", "true", "yes"}


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

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_database():
    conn = get_connection()
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
