from models.user import User


class Worker(User):
    def __init__(self, user_id=None, username="", password_hash="", full_name=""):
        super().__init__(user_id=user_id, username=username, password_hash=password_hash, full_name=full_name, role="WORKER")

    def register_vehicle(self):
        return "Worker can register vehicle and allocate slot."
