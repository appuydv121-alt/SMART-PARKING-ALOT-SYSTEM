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

    def create_user(self, username: str, full_name: str, password: str, role: str, account_status: str = 'ACTIVE', created_by: int = None):
        conn = get_connection()
        existing = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            conn.close()
            raise ValueError(f"User '{username}' already exists.")
        password_hash = User.hash_password(password)
        cur = conn.execute(
            "INSERT INTO users (username, password_hash, full_name, role, account_status, plain_password, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, password_hash, full_name, role.upper(), account_status, password, created_by),
        )
        conn.commit()
        user_id = cur.lastrowid
        conn.close()
        return user_id

    def update_password(self, user_id: int, new_password: str):
        if not new_password or len(new_password) < 4:
            raise ValueError("New password must be at least 4 characters.")
        password_hash = User.hash_password(new_password)
        conn = get_connection()
        conn.execute(
            "UPDATE users SET password_hash = ?, plain_password = ? WHERE user_id = ?",
            (password_hash, new_password, user_id),
        )
        conn.commit()
        conn.close()

    def verify_admin_password(self, admin_id: int, admin_password: str) -> bool:
        conn = get_connection()
        row = conn.execute("SELECT password_hash FROM users WHERE user_id = ? AND role = 'ADMIN'", (admin_id,)).fetchone()
        conn.close()
        if row is None:
            return False
        return User.verify_password(admin_password, row['password_hash'])
