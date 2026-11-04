from models.user import User


class Admin(User):
    def __init__(self, user_id=None, username="", password_hash="", full_name=""):
        super().__init__(user_id=user_id, username=username, password_hash=password_hash, full_name=full_name, role="ADMIN")

    def configure_parking_facility(self):
        return "Admin can configure the parking lot and rates."
