from database.connection import get_connection


class WorkerManagementService:
    def create_worker(self, username: str, password: str, full_name: str):
        from services.auth_service import AuthenticationService
        service = AuthenticationService()
        return service.create_user(username=username, full_name=full_name, password=password, role='WORKER')

    def list_workers(self):
        conn = get_connection()
        rows = conn.execute("SELECT * FROM users WHERE role = 'WORKER' ORDER BY created_at").fetchall()
        conn.close()
        return [dict(row) for row in rows]
