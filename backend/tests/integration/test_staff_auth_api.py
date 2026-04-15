"""Integration tests for staff authentication API."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.staff.auth import router
from src.security.auth import hash_password


def _create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router, prefix="/v1/staff/auth")
    return app


def _make_staff_row(employee_id: str = "NV001", password: str = "password123", is_active: bool = True):
    """Create a mock StaffMember row."""
    staff = MagicMock()
    staff.id = uuid.uuid4()
    staff.employee_id = employee_id
    staff.full_name = "Nguyễn Văn An"
    staff.department_id = uuid.uuid4()
    staff.clearance_level = 1
    staff.role = "officer"
    staff.is_active = is_active
    staff.password_hash = hash_password(password)
    return staff


class TestStaffLogin:
    """Test POST /v1/staff/auth/login."""

    @patch("src.api.staff.auth.get_db")
    def test_login_success(self, mock_get_db):
        """Valid credentials should return access_token, refresh_token, staff info."""
        staff = _make_staff_row()

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = staff
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_get_db.return_value = mock_session

        app = _create_app()
        app.dependency_overrides[mock_get_db] = lambda: mock_session

        # Override the actual dependency
        from src.dependencies import get_db
        app.dependency_overrides[get_db] = lambda: mock_session

        client = TestClient(app)
        resp = client.post("/v1/staff/auth/login", json={
            "employee_id": "NV001",
            "password": "password123",
        })

        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "expires_in" in data
        assert data["staff"]["full_name"] == "Nguyễn Văn An"
        assert data["staff"]["clearance_level"] == 1
        assert data["staff"]["role"] == "officer"

    @patch("src.api.staff.auth.get_db")
    def test_login_wrong_password(self, mock_get_db):
        """Wrong password should return 401."""
        staff = _make_staff_row(password="correct_password")

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = staff
        mock_session.execute = AsyncMock(return_value=mock_result)

        from src.dependencies import get_db
        app = _create_app()
        app.dependency_overrides[get_db] = lambda: mock_session

        client = TestClient(app)
        resp = client.post("/v1/staff/auth/login", json={
            "employee_id": "NV001",
            "password": "wrong_password",
        })

        assert resp.status_code == 401
        assert resp.json()["detail"] == "Employee ID or password is incorrect."

    @patch("src.api.staff.auth.get_db")
    def test_login_nonexistent_employee(self, mock_get_db):
        """Non-existent employee ID should return 401."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        from src.dependencies import get_db
        app = _create_app()
        app.dependency_overrides[get_db] = lambda: mock_session

        client = TestClient(app)
        resp = client.post("/v1/staff/auth/login", json={
            "employee_id": "INVALID",
            "password": "password123",
        })

        assert resp.status_code == 401
        assert resp.json()["detail"] == "Employee ID or password is incorrect."

    def test_login_missing_fields(self):
        """Missing required fields should return 422."""
        app = _create_app()
        client = TestClient(app)

        resp = client.post("/v1/staff/auth/login", json={})
        assert resp.status_code == 422

        resp = client.post("/v1/staff/auth/login", json={"employee_id": "NV001"})
        assert resp.status_code == 422

        resp = client.post("/v1/staff/auth/login", json={"password": "pass"})
        assert resp.status_code == 422

    @patch("src.api.staff.auth.get_db")
    def test_login_token_is_valid_jwt(self, mock_get_db):
        """Returned token should be a valid JWT with expected claims."""
        staff = _make_staff_row()

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = staff
        mock_session.execute = AsyncMock(return_value=mock_result)

        from src.dependencies import get_db
        app = _create_app()
        app.dependency_overrides[get_db] = lambda: mock_session

        client = TestClient(app)
        resp = client.post("/v1/staff/auth/login", json={
            "employee_id": "NV001",
            "password": "password123",
        })

        data = resp.json()
        from src.security.auth import decode_token
        payload = decode_token(data["access_token"])
        assert payload["type"] == "staff"
        assert payload["employee_id"] == "NV001"
        assert payload["clearance_level"] == 1
