CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('ADMIN', 'WORKER')),
    account_status TEXT NOT NULL DEFAULT 'ACTIVE',
    plain_password TEXT,
    created_by INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS parking_lots (
    lot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lot_name TEXT NOT NULL,
    location TEXT NOT NULL,
    created_by INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS parking_slots (
    slot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lot_id INTEGER NOT NULL,
    slot_number TEXT NOT NULL,
    slot_type TEXT NOT NULL CHECK(slot_type IN ('CAR', 'BIKE')),
    occupancy_status TEXT NOT NULL DEFAULT 'AVAILABLE' CHECK(occupancy_status IN ('AVAILABLE', 'OCCUPIED')),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(lot_id, slot_number),
    FOREIGN KEY (lot_id) REFERENCES parking_lots(lot_id)
);

CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_number TEXT UNIQUE NOT NULL,
    owner_name TEXT NOT NULL,
    vehicle_type TEXT NOT NULL CHECK(vehicle_type IN ('CAR', 'BIKE')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS parking_rates (
    rate_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lot_id INTEGER NOT NULL,
    vehicle_type TEXT NOT NULL CHECK(vehicle_type IN ('CAR', 'BIKE')),
    hourly_rate REAL NOT NULL,
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (lot_id) REFERENCES parking_lots(lot_id)
);

CREATE TABLE IF NOT EXISTS parking_records (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id TEXT UNIQUE NOT NULL,
    vehicle_id INTEGER NOT NULL,
    slot_id INTEGER NOT NULL,
    entry_worker_id INTEGER NOT NULL,
    exit_worker_id INTEGER,
    entry_time TEXT NOT NULL,
    exit_time TEXT,
    applied_hourly_rate REAL NOT NULL,
    chargeable_duration INTEGER DEFAULT 0,
    total_fee REAL DEFAULT 0,
    parking_status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(parking_status IN ('ACTIVE', 'COMPLETED', 'CANCELLED')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
    FOREIGN KEY (slot_id) REFERENCES parking_slots(slot_id),
    FOREIGN KEY (entry_worker_id) REFERENCES users(user_id),
    FOREIGN KEY (exit_worker_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    payment_method TEXT NOT NULL CHECK(payment_method IN ('CASH', 'UPI', 'CARD')),
    payment_status TEXT NOT NULL CHECK(payment_status IN ('PENDING', 'SUCCESS', 'FAILED')),
    processed_by INTEGER NOT NULL,
    payment_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    transaction_reference TEXT,
    FOREIGN KEY (record_id) REFERENCES parking_records(record_id),
    FOREIGN KEY (processed_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS receipts (
    receipt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id INTEGER NOT NULL,
    receipt_number TEXT UNIQUE NOT NULL,
    receipt_type TEXT NOT NULL CHECK(receipt_type IN ('ENTRY', 'EXIT')),
    file_path TEXT,
    created_by INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (record_id) REFERENCES parking_records(record_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);
