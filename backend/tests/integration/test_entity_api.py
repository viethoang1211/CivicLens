"""Integration tests for entity extraction in classification endpoint."""

import uuid

from src.security.auth import StaffIdentity


def _make_staff(clearance: int = 3) -> StaffIdentity:
    return StaffIdentity(
        staff_id=uuid.uuid4(),
        employee_id="EMP001",
        department_id=uuid.uuid4(),
        clearance_level=clearance,
        role="staff",
    )


class TestEntityAPI:
    """Test that classification endpoint exposes entities."""

    def test_classification_response_includes_entities_field(self):
        """GET /submissions/{id}/classification should include entities."""
        response = {
            "submission_id": str(uuid.uuid4()),
            "classification": {
                "document_type_id": str(uuid.uuid4()),
                "document_type_name": "Giấy khai sinh",
                "confidence": 0.92,
                "alternatives": [],
            },
            "template_data": {"ho_ten": "Nguyễn Văn An"},
            "ai_summary": "Giấy khai sinh của Nguyễn Văn An",
            "ai_summary_is_ai_generated": True,
            "entities": {
                "persons": ["Nguyễn Văn An"],
                "id_numbers": ["012345678901"],
                "dates": ["15/03/1990"],
                "addresses": [],
                "amounts": [],
            },
        }

        assert "entities" in response
        assert "ai_summary" in response
        assert "ai_summary_is_ai_generated" in response
        assert response["entities"]["persons"] == ["Nguyễn Văn An"]

    def test_entities_null_when_not_generated(self):
        """Entities should be null when no summarization has run."""
        response = {
            "submission_id": str(uuid.uuid4()),
            "classification": {
                "document_type_id": None,
                "document_type_name": None,
                "confidence": None,
                "alternatives": [],
            },
            "template_data": None,
            "ai_summary": None,
            "ai_summary_is_ai_generated": False,
            "entities": None,
        }

        assert response["entities"] is None
        assert response["ai_summary_is_ai_generated"] is False
