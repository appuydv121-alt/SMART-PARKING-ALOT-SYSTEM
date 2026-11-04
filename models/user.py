import hashlib
import os


class User:
    def __init__(self, user_id=None, username="", password_hash="", full_name="", role="WORKER"):
        self.user_id = user_id
        self.username = username
        self.password_hash = password_hash
        self.full_name = full_name
        self.role = role.upper()

    @staticmethod
    def hash_password(password: str) -> str:
        salt = os.urandom(16).hex()
        digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 200000)
        return f"{salt}:{digest.hex()}"

    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        if not stored_hash or ':' not in stored_hash:
            return False
        salt, expected = stored_hash.split(':', 1)
        candidate = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 200000)
        return candidate.hex() == expected

    def set_password(self, password: str):
        self.password_hash = self.hash_password(password)
        return self.password_hash

    def check_password(self, password: str) -> bool:
        return self.verify_password(password, self.password_hash)

    def to_row(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'password_hash': self.password_hash,
            'full_name': self.full_name,
            'role': self.role,
        }

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            user_id=row.get('user_id'),
            username=row.get('username'),
            password_hash=row.get('password_hash'),
            full_name=row.get('full_name'),
            role=row.get('role'),
        )
