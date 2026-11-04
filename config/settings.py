import os

DB_HOST = os.getenv("SMART_PARKING_DB_HOST", "localhost")
DB_PORT = int(os.getenv("SMART_PARKING_DB_PORT", "3306"))
DB_USER = os.getenv("SMART_PARKING_DB_USER", "root")
DB_PASSWORD = os.getenv("SMART_PARKING_DB_PASSWORD", "Arpit@2007")
DB_NAME = os.getenv("SMART_PARKING_DB_NAME", "smart_parking")
USE_MYSQL = os.getenv("SMART_PARKING_USE_MYSQL", "false").lower() in {"1", "true", "yes"}
APP_NAME = "Smart Parking Lot Management System"
