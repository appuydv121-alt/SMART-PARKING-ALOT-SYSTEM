import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from database import connection


def test_turso_connection_uses_remote_driver(monkeypatch):
    remote_connection = Mock()
    remote_driver = SimpleNamespace(connect=Mock(return_value=remote_connection), Row=object)
    monkeypatch.setattr(connection, "TURSO_DATABASE_URL", "libsql://parking.turso.io")
    monkeypatch.setattr(connection, "TURSO_AUTH_TOKEN", "test-token")
    monkeypatch.setattr(connection, "REQUIRE_TURSO", False)
    monkeypatch.setitem(sys.modules, "turso_serverless", remote_driver)

    result = connection.get_connection()

    assert result is remote_connection
    remote_driver.connect.assert_called_once_with(
        "libsql://parking.turso.io",
        auth_token="test-token",
    )
    assert remote_connection.row_factory is remote_driver.Row
    remote_connection.execute.assert_called_once_with("PRAGMA foreign_keys = ON")


def test_turso_connection_rejects_partial_credentials(monkeypatch):
    monkeypatch.setattr(connection, "TURSO_DATABASE_URL", "libsql://parking.turso.io")
    monkeypatch.setattr(connection, "TURSO_AUTH_TOKEN", None)
    monkeypatch.setattr(connection, "REQUIRE_TURSO", False)

    with pytest.raises(RuntimeError, match="Both TURSO_DATABASE_URL and TURSO_AUTH_TOKEN"):
        connection.get_connection()


def test_required_turso_does_not_fall_back_to_local_sqlite(monkeypatch):
    monkeypatch.setattr(connection, "TURSO_DATABASE_URL", None)
    monkeypatch.setattr(connection, "TURSO_AUTH_TOKEN", None)
    monkeypatch.setattr(connection, "REQUIRE_TURSO", True)

    with pytest.raises(RuntimeError, match="Turso is required"):
        connection.get_connection()
