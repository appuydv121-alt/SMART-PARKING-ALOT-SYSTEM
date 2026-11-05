from database.connection import get_connection


class WorkerManagementService:
    def create_worker(self, username: str, password: str, full_name: str, created_by: int = None):
        from services.auth_service import AuthenticationService
        service = AuthenticationService()
        return service.create_user(username=username, full_name=full_name, password=password, role='WORKER', created_by=created_by)

    def list_workers(self, admin_id: int = None):
        conn = get_connection()
        if admin_id is not None:
            if admin_id == 1:
                rows = conn.execute(
                    "SELECT * FROM users WHERE role = 'WORKER' AND account_status = 'ACTIVE' AND (created_by = 1 OR created_by IS NULL) ORDER BY created_at"
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM users WHERE role = 'WORKER' AND account_status = 'ACTIVE' AND created_by = ? ORDER BY created_at",
                    (admin_id,)
                ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM users WHERE role = 'WORKER' AND account_status = 'ACTIVE' ORDER BY created_at").fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def remove_worker(self, worker_id: int, worker_password: str, admin_id: int):
        conn = get_connection()
        try:
            if admin_id == 1:
                row = conn.execute(
                    "SELECT user_id, username, password_hash FROM users WHERE user_id = ? AND role = 'WORKER' AND (created_by = 1 OR created_by IS NULL)",
                    (worker_id,)
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT user_id, username, password_hash FROM users WHERE user_id = ? AND role = 'WORKER' AND created_by = ?",
                    (worker_id, admin_id)
                ).fetchone()

            if not row:
                raise ValueError("Worker not found or not managed by you.")

            from models.user import User
            if not User.verify_password(worker_password, row['password_hash']):
                raise ValueError("Incorrect worker password. Verification failed.")

            # Try deleting worker from database
            try:
                conn.execute("DELETE FROM users WHERE user_id = ?", (worker_id,))
                conn.commit()
            except Exception:
                conn.execute("UPDATE users SET account_status = 'INACTIVE' WHERE user_id = ?", (worker_id,))
                conn.commit()

            return {'success': True, 'username': row['username']}
        finally:
            conn.close()
