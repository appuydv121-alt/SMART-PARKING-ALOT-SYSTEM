from database.connection import get_connection
from models.user import User


class AuthenticationService:
    def login(self, username: str, password: str):
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? AND account_status = 'ACTIVE'",
            (username,),
        ).fetchone()
        conn.close()
        if row is None:
            raise ValueError("Invalid username or password.")
        if not User.verify_password(password, row['password_hash']):
            raise ValueError("Invalid username or password.")
        return User.from_row(dict(row))

    def create_user(self, username: str, full_name: str, password: str, role: str, account_status: str = 'ACTIVE'):
        conn = get_connection()
        existing = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            conn.close()
            raise ValueError(f"User '{username}' already exists.")
        password_hash = User.hash_password(password)
        cur = conn.execute(
            "INSERT INTO users (username, password_hash, full_name, role, account_status) VALUES (?, ?, ?, ?, ?)",
            (username, password_hash, full_name, role.upper(), account_status),
        )
        conn.commit()
        user_id = cur.lastrowid
        conn.close()
        return user_id
