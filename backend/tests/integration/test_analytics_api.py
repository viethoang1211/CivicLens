"""Integration tests for analytics API endpoint."""

import uuid
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.staff.analytics import router
from src.security.auth import StaffIdentity, get_current_staff


def _make_staff(role: str = "manager", clearance: int = 3) -> StaffIdentity:
    return StaffIdentity(
        staff_id=uuid.uuid4(),
        employee_id="EMP001",
        department_id=uuid.uuid4(),
        clearance_level=clearance,
        role=role,
    )


def _create_app(staff: StaffIdentity | None = None) -> FastAPI:
    app = FastAPI()
    app.include_router(router, prefix="/v1/staff/analytics")
    if staff is None:
        staff = _make_staff()
    app.dependency_overrides[get_current_staff] = lambda: staff
    return app


class TestAnalyticsAPI:
    """Test GET /v1/staff/analytics/sla endpoint."""

    @patch("src.api.staff.analytics.analytics_service.get_sla_metrics")
    def test_200_for_manager(self, mock_metrics):
        """Manager role should get 200."""
        mock_metrics.return_value = {
            "period": {"from": "2026-03-16", "to": "2026-04-15"},
            "departments": [],
            "totals": {
                "total_steps": 0,
                "completed_steps": 0,
                "pending_steps": 0,
                "delayed_steps": 0,
                "avg_processing_hours": 0.0,
                "delay_rate": 0.0,
                "completion_rate": 0.0,
            },
        }

        app = _create_app(_make_staff("manager"))
        client = TestClient(app)
        resp = client.get("/v1/staff/analytics/sla")
        assert resp.status_code == 200
        data = resp.json()
        assert "period" in data
        assert "departments" in data
        assert "totals" in data

    def test_403_for_non_manager(self):
        """Non-manager role should get 403."""
        app = _create_app(_make_staff("staff"))
        client = TestClient(app)
        resp = client.get("/v1/staff/analytics/sla")
        assert resp.status_code == 403

    @patch("src.api.staff.analytics.analytics_service.get_sla_metrics")
    def test_200_for_admin(self, mock_metrics):
        """Admin role should also get 200."""
        mock_metrics.return_value = {
            "period": {"from": "2026-03-16", "to": "2026-04-15"},
            "departments": [],
            "totals": {
                "total_steps": 0, "completed_steps": 0, "pending_steps": 0,
                "delayed_steps": 0, "avg_processing_hours": 0.0,
                "delay_rate": 0.0, "completion_rate": 0.0,
            },
        }
        app = _create_app(_make_staff("admin"))
        client = TestClient(app)
        resp = client.get("/v1/staff/analytics/sla")
        assert resp.status_code == 200

    @patch("src.api.staff.analytics.analytics_service.get_sla_metrics")
    def test_response_has_no_citizen_pii(self, mock_metrics):
        """Analytics response should not contain citizen PII."""
        mock_metrics.return_value = {
            "period": {"from": "2026-03-16", "to": "2026-04-15"},
            "departments": [
                {
                    "department_id": str(uuid.uuid4()),
                    "department_name": "Phòng Tư pháp",
                    "department_code": "JUSTICE",
                    "metrics": {
                        "total_steps": 50,
                        "completed_steps": 40,
                        "pending_steps": 8,
                        "delayed_steps": 2,
                        "avg_processing_hours": 3.5,
                        "delay_rate": 0.04,
                        "completion_rate": 0.8,
                    },
                }
            ],
            "totals": {
                "total_steps": 50, "completed_steps": 40, "pending_steps": 8,
                "delayed_steps": 2, "avg_processing_hours": 3.5,
                "delay_rate": 0.04, "completion_rate": 0.8,
            },
        }

        app = _create_app(_make_staff("manager"))
        client = TestClient(app)
        resp = client.get("/v1/staff/analytics/sla")
        data = resp.json()

        # Serialize to string and check no PII-like fields
        data_str = str(data)
        pii_fields = ["citizen_name", "full_name", "id_number", "phone_number", "email", "vneid"]
        for field in pii_fields:
            assert field not in data_str, f"Response should not contain PII field: {field}"
