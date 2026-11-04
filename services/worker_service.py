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
                    "SELECT * FROM users WHERE role = 'WORKER' AND (created_by = 1 OR created_by IS NULL) ORDER BY created_at"
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM users WHERE role = 'WORKER' AND created_by = ? ORDER BY created_at",
                    (admin_id,)
                ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM users WHERE role = 'WORKER' ORDER BY created_at").fetchall()
        conn.close()
        return [dict(row) for row in rows]
