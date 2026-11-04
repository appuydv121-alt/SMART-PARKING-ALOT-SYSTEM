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

    lot_exists = conn.execute("SELECT 1 FROM parking_lots WHERE lot_name = 'City Parking'").fetchone()
    if lot_exists is None:
        admin = conn.execute("SELECT user_id FROM users WHERE username = 'admin'").fetchone()
        if admin is not None:
            conn.execute(
                "INSERT INTO parking_lots (lot_name, location, created_by) VALUES (?, ?, ?)",
                ('City Parking', 'Main Market', admin['user_id']),
            )
    conn.commit()
    conn.close()
