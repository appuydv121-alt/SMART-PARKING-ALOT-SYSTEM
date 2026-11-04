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
