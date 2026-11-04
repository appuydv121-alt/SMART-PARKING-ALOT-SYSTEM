import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "smart_parking.db"
SCHEMA_PATH = ROOT / "database" / "schema.sql"


def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_database():
    conn = get_connection()
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(sql)

    try:
        conn.execute("ALTER TABLE users ADD COLUMN plain_password TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        conn.execute("ALTER TABLE users ADD COLUMN created_by INTEGER")
    except sqlite3.OperationalError:
        pass

    try:
        conn.execute("UPDATE users SET plain_password = 'admin123' WHERE username = 'admin' AND (plain_password IS NULL OR plain_password = '')")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


def initialize_database():
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
