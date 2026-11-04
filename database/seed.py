from database.connection import get_connection


def seed_default_data():
    conn = get_connection()
    admin_exists = conn.execute("SELECT 1 FROM users WHERE username = 'admin'").fetchone()
    if admin_exists is None:
        from services.auth_service import AuthenticationService
        service = AuthenticationService()
        service.create_user(
            username='admin',
            full_name='System Administrator',
            password='admin123',
            role='ADMIN',
        )

    # Ensure exactly one single primary parking lot exists
    lot_row = conn.execute("SELECT lot_id FROM parking_lots ORDER BY lot_id ASC LIMIT 1").fetchone()
    if lot_row is None:
        admin = conn.execute("SELECT user_id FROM users WHERE username = 'admin'").fetchone()
        admin_id = admin['user_id'] if admin is not None else 1
        cur = conn.execute(
            "INSERT INTO parking_lots (lot_name, location, created_by) VALUES (?, ?, ?)",
            ('City Parking', 'Main Market', admin_id),
        )
        lot_id = cur.lastrowid
    else:
        lot_id = lot_row['lot_id']

    # Ensure default rates exist for the lot
    car_rate = conn.execute("SELECT 1 FROM parking_rates WHERE lot_id = ? AND vehicle_type = 'CAR'", (lot_id,)).fetchone()
    if car_rate is None:
        conn.execute(
            "INSERT INTO parking_rates (lot_id, vehicle_type, hourly_rate, effective_from, is_active) VALUES (?, 'CAR', 30.0, datetime('now'), 1)",
            (lot_id,),
        )
    bike_rate = conn.execute("SELECT 1 FROM parking_rates WHERE lot_id = ? AND vehicle_type = 'BIKE'", (lot_id,)).fetchone()
    if bike_rate is None:
        conn.execute(
            "INSERT INTO parking_rates (lot_id, vehicle_type, hourly_rate, effective_from, is_active) VALUES (?, 'BIKE', 15.0, datetime('now'), 1)",
            (lot_id,),
        )

    # Ensure default slots exist if lot is empty
    slot_count = conn.execute("SELECT COUNT(*) FROM parking_slots WHERE lot_id = ?", (lot_id,)).fetchone()[0]
    if slot_count == 0:
        for index in range(1, 21):
            conn.execute(
                "INSERT OR IGNORE INTO parking_slots (lot_id, slot_number, slot_type, occupancy_status, is_active) VALUES (?, ?, 'CAR', 'AVAILABLE', 1)",
                (lot_id, f"C-{index:02d}"),
            )
        for index in range(1, 31):
            conn.execute(
                "INSERT OR IGNORE INTO parking_slots (lot_id, slot_number, slot_type, occupancy_status, is_active) VALUES (?, ?, 'BIKE', 'AVAILABLE', 1)",
                (lot_id, f"B-{index:02d}"),
            )

    conn.commit()
    conn.close()
