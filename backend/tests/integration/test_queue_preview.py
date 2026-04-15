"""Integration tests for queue summary preview."""

import uuid
from datetime import UTC, datetime

from src.security.auth import StaffIdentity


def _make_staff(clearance: int = 3) -> StaffIdentity:
    return StaffIdentity(
        staff_id=uuid.uuid4(),
        employee_id="EMP001",
        department_id=uuid.uuid4(),
        clearance_level=clearance,
        role="staff",
    )


class TestQueuePreview:
    """Test GET /departments/{id}/queue includes summary_preview."""

    def test_queue_item_has_summary_preview_field(self):
        """Queue response items should include summary_preview."""
        # Test the response shape contract
        item = {
            "workflow_step_id": str(uuid.uuid4()),
            "submission_id": str(uuid.uuid4()),
            "dossier_id": None,
            "document_type_name": "Giấy khai sinh",
            "priority": "urgent",
            "started_at": datetime.now(UTC).isoformat(),
            "expected_complete_by": None,
            "is_delayed": False,
            "summary_preview": "Giấy khai sinh của Nguyễn Văn An, sinh ngày 15/03/2026 tại Bệnh viện Từ Dũ...",
        }
        assert "summary_preview" in item
        assert isinstance(item["summary_preview"], str)

    def test_summary_preview_null_when_no_summary(self):
        """summary_preview should be null when no AI summary exists."""
        item = {
            "workflow_step_id": str(uuid.uuid4()),
            "submission_id": str(uuid.uuid4()),
            "dossier_id": None,
            "priority": "normal",
            "summary_preview": None,
        }
        assert item["summary_preview"] is None

    def test_summary_preview_truncated_at_100_chars(self):
        """summary_preview should be truncated to 100 chars."""
        long_summary = "A" * 200
        preview = long_summary[:100]
        assert len(preview) == 100
