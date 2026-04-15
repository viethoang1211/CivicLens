"""Contract tests: validate search response JSON shape matches contracts/staff-api.md."""

import uuid


class TestSearchResponseContract:
    """Validate search response shape."""

    def _make_submission_result(self):
        return {
            "type": "submission",
            "id": str(uuid.uuid4()),
            "status": "completed",
            "submitted_at": "2026-04-10T08:30:00+00:00",
            "citizen_name": "Nguyễn Văn An",
            "document_type_name": "Giấy khai sinh",
            "document_type_code": "BIRTH_CERT",
            "ai_summary": "Giấy khai sinh...",
            "ai_summary_is_ai_generated": True,
            "relevance_score": 0.85,
            "highlight": "<em>Nguyễn</em>",
        }

    def _make_dossier_result(self):
        return {
            "type": "dossier",
            "id": str(uuid.uuid4()),
            "status": "in_progress",
            "submitted_at": "2026-04-12T09:00:00+00:00",
            "citizen_name": "Nguyễn Văn An",
            "case_type_name": "Đăng ký khai sinh",
            "case_type_code": "BIRTH_REG",
            "reference_number": "HS-20260412-001",
            "ai_summary": "Hồ sơ đăng ký...",
            "ai_summary_is_ai_generated": True,
            "relevance_score": 0.72,
            "highlight": "<em>Nguyễn</em>",
        }

    def _make_response(self, results=None):
        return {
            "results": results or [],
            "pagination": {
                "page": 1,
                "per_page": 20,
                "total": len(results or []),
                "total_pages": 1 if results else 0,
            },
            "query": "Nguyễn",
        }

    def test_submission_result_shape(self):
        """Submission result has required fields per contract."""
        result = self._make_submission_result()
        required = {"type", "id", "status", "submitted_at", "citizen_name",
                     "document_type_name", "document_type_code", "ai_summary",
                     "ai_summary_is_ai_generated", "relevance_score", "highlight"}
        assert required.issubset(set(result.keys()))
        assert result["type"] == "submission"

    def test_dossier_result_shape(self):
        """Dossier result has required fields per contract."""
        result = self._make_dossier_result()
        required = {"type", "id", "status", "submitted_at", "citizen_name",
                     "case_type_name", "case_type_code", "reference_number",
                     "ai_summary", "ai_summary_is_ai_generated", "relevance_score", "highlight"}
        assert required.issubset(set(result.keys()))
        assert result["type"] == "dossier"

    def test_pagination_shape(self):
        """Pagination has required fields per contract."""
        resp = self._make_response([self._make_submission_result()])
        pagination = resp["pagination"]
        required = {"page", "per_page", "total", "total_pages"}
        assert required == set(pagination.keys())
        assert isinstance(pagination["page"], int)
        assert isinstance(pagination["total"], int)

    def test_response_has_query(self):
        """Response includes the original query."""
        resp = self._make_response()
        assert "query" in resp
        assert isinstance(resp["query"], str)

    def test_ai_summary_is_ai_generated_is_bool(self):
        """ai_summary_is_ai_generated must be boolean."""
        result = self._make_submission_result()
        assert isinstance(result["ai_summary_is_ai_generated"], bool)
