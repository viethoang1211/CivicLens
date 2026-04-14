"""Integration test: full pipeline for submission and dossier workflows.

Uses mocked AI client and database session to trace the complete call path
from review through workflow advancement, notifications, and completion.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.workflow_service import advance_workflow


class TestFullSubmissionPipeline:
    """Trace: review → advance_workflow → completion for submission mode."""

    @pytest.mark.asyncio
    async def test_submission_approve_advance_complete(self):
        """Multi-step submission: approve step 1 → advance → approve step 2 → completed."""
        db = AsyncMock()

        submission = MagicMock()
        submission.id = uuid.uuid4()
        submission.citizen_id = uuid.uuid4()
        submission.document_type_id = uuid.uuid4()
        submission.status = "in_progress"

        dept = MagicMock()
        dept.name = "Phòng Tư pháp"

        # --- Step 1: Approve → advances to step 2 ---
        step1 = MagicMock()
        step1.submission_id = submission.id
        step1.dossier_id = None
        step1.step_order = 1

        step2 = MagicMock()
        step2.step_order = 2
        step2.department_id = uuid.uuid4()
        step2.status = "pending"

        sub_result = MagicMock()
        sub_result.scalar_one.return_value = submission
        next_result = MagicMock()
        next_result.scalar_one_or_none.return_value = step2
        rule_result = MagicMock()
        rule_result.scalar_one_or_none.return_value = None
        dept_result = MagicMock()
        dept_result.scalar_one_or_none.return_value = dept

        db.execute.side_effect = [sub_result, next_result, rule_result, dept_result]

        with patch("src.services.workflow_service.notify_step_advanced", new_callable=AsyncMock):
            result1 = await advance_workflow(db, step1, "approved")

        assert result1["action"] == "advanced"
        assert step2.status == "active"

        # --- Step 2: Approve → no more steps → completed ---
        step2.submission_id = submission.id
        step2.dossier_id = None

        sub_result2 = MagicMock()
        sub_result2.scalar_one.return_value = submission
        no_next = MagicMock()
        no_next.scalar_one_or_none.return_value = None

        db.execute.side_effect = [sub_result2, no_next]

        with (
            patch("src.services.workflow_service.notify_completed", new_callable=AsyncMock) as mock_complete,
            patch("src.services.workflow_service._set_retention_expiry", new_callable=AsyncMock),
        ):
            result2 = await advance_workflow(db, step2, "approved")

        assert result2["action"] == "completed"
        assert submission.status == "completed"
        mock_complete.assert_called_once()


class TestFullDossierPipeline:
    """Trace: review → advance_workflow → completion for dossier mode."""

    @pytest.mark.asyncio
    async def test_dossier_approve_advance_complete(self):
        """Multi-step dossier: approve step 1 → advance → approve step 2 → completed."""
        db = AsyncMock()

        dossier = MagicMock()
        dossier.id = uuid.uuid4()
        dossier.citizen_id = uuid.uuid4()
        dossier.case_type_id = uuid.uuid4()
        dossier.reference_number = "HS-20250614-00001"
        dossier.status = "in_progress"
        dossier.rejection_reason = None

        dept = MagicMock()
        dept.name = "Phòng Cảnh sát"

        # --- Step 1: Approve → advances to step 2 ---
        step1 = MagicMock()
        step1.submission_id = None
        step1.dossier_id = dossier.id
        step1.step_order = 1

        step2 = MagicMock()
        step2.step_order = 2
        step2.department_id = uuid.uuid4()
        step2.status = "pending"

        dos_result = MagicMock()
        dos_result.scalar_one.return_value = dossier
        next_result = MagicMock()
        next_result.scalar_one_or_none.return_value = step2
        routing_result = MagicMock()
        routing_result.scalar_one_or_none.return_value = None
        dept_result = MagicMock()
        dept_result.scalar_one_or_none.return_value = dept

        db.execute.side_effect = [dos_result, next_result, routing_result, dept_result]

        with patch("src.services.workflow_service.notify_dossier_step_advanced", new_callable=AsyncMock):
            result1 = await advance_workflow(db, step1, "approved")

        assert result1["action"] == "advanced"
        assert step2.status == "active"

        # --- Step 2: Approve → no more steps → completed ---
        step2.submission_id = None
        step2.dossier_id = dossier.id

        dos_result2 = MagicMock()
        dos_result2.scalar_one.return_value = dossier
        no_next = MagicMock()
        no_next.scalar_one_or_none.return_value = None

        db.execute.side_effect = [dos_result2, no_next]

        with (
            patch("src.services.workflow_service.notify_dossier_status_change", new_callable=AsyncMock) as mock_status,
            patch("src.services.workflow_service._set_dossier_retention_expiry", new_callable=AsyncMock) as mock_retention,
        ):
            result2 = await advance_workflow(db, step2, "approved")

        assert result2["action"] == "completed"
        assert dossier.status == "completed"
        mock_status.assert_called_once_with(db, dossier.id, "completed")
        mock_retention.assert_called_once()

    @pytest.mark.asyncio
    async def test_dossier_reject_with_reason(self):
        """Dossier rejected at step 1 → notification with rejection reason."""
        db = AsyncMock()

        dossier = MagicMock()
        dossier.id = uuid.uuid4()
        dossier.reference_number = "HS-20250614-00002"
        dossier.status = "in_progress"
        dossier.rejection_reason = "Thiếu giấy chứng sinh"

        step1 = MagicMock()
        step1.submission_id = None
        step1.dossier_id = dossier.id
        step1.step_order = 1

        dos_result = MagicMock()
        dos_result.scalar_one.return_value = dossier
        db.execute.side_effect = [dos_result]

        with patch("src.services.workflow_service.notify_dossier_status_change", new_callable=AsyncMock) as mock_notify:
            result = await advance_workflow(db, step1, "rejected")

        assert result["action"] == "rejected"
        assert dossier.status == "rejected"
        mock_notify.assert_called_once_with(db, dossier.id, "rejected", "Thiếu giấy chứng sinh")
