"""Integration tests for search API endpoint."""

import uuid
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.staff.search import router
from src.security.auth import StaffIdentity, get_current_staff


def _make_staff(clearance: int = 3, role: str = "staff") -> StaffIdentity:
    return StaffIdentity(
        staff_id=uuid.uuid4(),
        employee_id="EMP001",
        department_id=uuid.uuid4(),
        clearance_level=clearance,
        role=role,
    )


def _create_app(staff: StaffIdentity | None = None) -> FastAPI:
    app = FastAPI()
    app.include_router(router, prefix="/v1/staff/search")
    if staff is None:
        staff = _make_staff()
    app.dependency_overrides[get_current_staff] = lambda: staff
    return app


class TestSearchAPI:
    """Test GET /v1/staff/search endpoint."""

    def test_422_on_short_query(self):
        """Query less than 2 chars should return 422."""
        app = _create_app()
        client = TestClient(app)
        resp = client.get("/v1/staff/search?q=a")
        assert resp.status_code == 422

    @patch("src.api.staff.search.search_service.search")
    def test_valid_query_returns_results(self, mock_search):
        """A valid query should return search results structure."""
        mock_search.return_value = {
            "results": [
                {
                    "type": "submission",
                    "id": str(uuid.uuid4()),
                    "status": "completed",
                    "submitted_at": "2026-04-10T08:30:00+00:00",
                    "citizen_name": "Nguyễn Văn An",
                    "document_type_name": "Giấy khai sinh",
                    "document_type_code": "BIRTH_CERT",
                    "ai_summary": "Giấy khai sinh test",
                    "ai_summary_is_ai_generated": True,
                    "relevance_score": 0.85,
                    "highlight": "<em>Nguyễn</em>",
                }
            ],
            "pagination": {"page": 1, "per_page": 20, "total": 1, "total_pages": 1},
            "query": "Nguyễn",
        }

        app = _create_app()
        client = TestClient(app)
        resp = client.get("/v1/staff/search?q=Nguyễn")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert "pagination" in data
        assert data["query"] == "Nguyễn"
        assert len(data["results"]) == 1
        assert data["results"][0]["type"] == "submission"

    @patch("src.api.staff.search.search_service.search")
    def test_filter_combinations(self, mock_search):
        """Test passing multiple filter params."""
        mock_search.return_value = {
            "results": [],
            "pagination": {"page": 1, "per_page": 20, "total": 0, "total_pages": 0},
            "query": "test",
        }

        app = _create_app()
        client = TestClient(app)
        resp = client.get(
            "/v1/staff/search?q=test&status=completed&date_from=2026-01-01&date_to=2026-12-31&page=2&per_page=10"
        )
        assert resp.status_code == 200
        mock_search.assert_called_once()
        call_kwargs = mock_search.call_args
        assert call_kwargs.kwargs["status"] == "completed"
        assert call_kwargs.kwargs["page"] == 2
        assert call_kwargs.kwargs["per_page"] == 10
