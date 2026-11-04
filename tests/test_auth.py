from database.connection import initialize_database
from database.seed import seed_default_data
from services.auth_service import AuthenticationService


def setup_function():
    initialize_database()
    seed_default_data()


def test_admin_login_works():
    user = AuthenticationService().login('admin', 'admin123')
    assert user.username == 'admin'
    assert user.role == 'ADMIN'
