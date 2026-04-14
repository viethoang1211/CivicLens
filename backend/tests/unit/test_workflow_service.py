"""Unit tests for workflow_service advance_workflow dual-owner mode."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_submission_step():
    """Create a submission-owned workflow step."""
    step = MagicMock()
    step.submission_id = uuid.uuid4()
    step.dossier_id = None
    step.step_order = 1
    step.department_id = uuid.uuid4()
    step.status = "active"
    step.completed_at = None
    step.result = None
    return step


@pytest.fixture
def mock_dossier_step():
    """Create a dossier-owned workflow step."""
    step = MagicMock()
    step.submission_id = None
    step.dossier_id = uuid.uuid4()
    step.step_order = 1
    step.department_id = uuid.uuid4()
    step.status = "active"
    step.completed_at = None
    step.result = None
    return step


@pytest.fixture
def mock_submission():
    submission = MagicMock()
    submission.id = uuid.uuid4()
    submission.citizen_id = uuid.uuid4()
    submission.document_type_id = uuid.uuid4()
    submission.status = "in_progress"
    submission.completed_at = None
    submission.retention_expires_at = None
    return submission


@pytest.fixture
def mock_dossier():
    dossier = MagicMock()
    dossier.id = uuid.uuid4()
    dossier.citizen_id = uuid.uuid4()
    dossier.case_type_id = uuid.uuid4()
    dossier.reference_number = "HS-20250101-00001"
    dossier.status = "in_progress"
    dossier.completed_at = None
    dossier.retention_expires_at = None
    dossier.rejection_reason = None
    return dossier


class TestAdvanceWorkflowSubmissionMode:
    """Test advance_workflow with submission-owned steps (existing behavior)."""

    @pytest.mark.asyncio
    async def test_approve_advances_to_next_step(self, mock_submission_step, mock_submission):
        db = AsyncMock()

        next_step = MagicMock()
        next_step.step_order = 2
        next_step.department_id = uuid.uuid4()
        next_step.status = "pending"

        dept = MagicMock()
        dept.name = "Phòng Tư pháp"

        # Setup db.execute returns: submission, next_step, routing_rule, department
        sub_result = MagicMock()
        sub_result.scalar_one.return_value = mock_submission

        next_result = MagicMock()
        next_result.scalar_one_or_none.return_value = next_step

        rule_result = MagicMock()
        rule_result.scalar_one_or_none.return_value = None  # No routing rule

        dept_result = MagicMock()
        dept_result.scalar_one_or_none.return_value = dept

        db.execute.side_effect = [sub_result, next_result, rule_result, dept_result]

        with patch("src.services.workflow_service.notify_step_advanced", new_callable=AsyncMock) as mock_notify:
            from src.services.workflow_service import advance_workflow
            result = await advance_workflow(db, mock_submission_step, "approved")

        assert result["action"] == "advanced"
        assert result["next_step_order"] == 2
        assert next_step.status == "active"
        mock_notify.assert_called_once()

    @pytest.mark.asyncio
    async def test_reject_completes_submission(self, mock_submission_step, mock_submission):
        db = AsyncMock()

        sub_result = MagicMock()
        sub_result.scalar_one.return_value = mock_submission
        db.execute.side_effect = [sub_result]

        with patch("src.services.workflow_service.notify_completed", new_callable=AsyncMock) as mock_notify:
            from src.services.workflow_service import advance_workflow
            result = await advance_workflow(db, mock_submission_step, "rejected")

        assert result["action"] == "rejected"
        assert mock_submission.status == "rejected"
        mock_notify.assert_called_once()


class TestAdvanceWorkflowDossierMode:
    """Test advance_workflow with dossier-owned steps."""

    @pytest.mark.asyncio
    async def test_approve_advances_to_next_step(self, mock_dossier_step, mock_dossier):
        db = AsyncMock()

        next_step = MagicMock()
        next_step.step_order = 2
        next_step.department_id = uuid.uuid4()
        next_step.status = "pending"

        dept = MagicMock()
        dept.name = "Phòng Tư pháp"

        # Setup db.execute returns: dossier, next_step, routing_step, department
        dos_result = MagicMock()
        dos_result.scalar_one.return_value = mock_dossier

        next_result = MagicMock()
        next_result.scalar_one_or_none.return_value = next_step

        routing_result = MagicMock()
        routing_result.scalar_one_or_none.return_value = None

        dept_result = MagicMock()
        dept_result.scalar_one_or_none.return_value = dept

        db.execute.side_effect = [dos_result, next_result, routing_result, dept_result]

        with patch("src.services.workflow_service.notify_dossier_step_advanced", new_callable=AsyncMock) as mock_notify:
            from src.services.workflow_service import advance_workflow
            result = await advance_workflow(db, mock_dossier_step, "approved")

        assert result["action"] == "advanced"
        assert result["next_step_order"] == 2
        assert next_step.status == "active"
        mock_notify.assert_called_once()

    @pytest.mark.asyncio
    async def test_reject_sets_dossier_rejected(self, mock_dossier_step, mock_dossier):
        db = AsyncMock()

        dos_result = MagicMock()
        dos_result.scalar_one.return_value = mock_dossier
        db.execute.side_effect = [dos_result]

        with patch("src.services.workflow_service.notify_dossier_status_change", new_callable=AsyncMock) as mock_notify:
            from src.services.workflow_service import advance_workflow
            result = await advance_workflow(db, mock_dossier_step, "rejected")

        assert result["action"] == "rejected"
        assert mock_dossier.status == "rejected"
        mock_notify.assert_called_once_with(db, mock_dossier.id, "rejected", mock_dossier.rejection_reason)

    @pytest.mark.asyncio
    async def test_complete_last_step_sets_dossier_completed(self, mock_dossier_step, mock_dossier):
        db = AsyncMock()

        dos_result = MagicMock()
        dos_result.scalar_one.return_value = mock_dossier

        next_result = MagicMock()
        next_result.scalar_one_or_none.return_value = None  # No next step → complete

        db.execute.side_effect = [dos_result, next_result]

        with (
            patch("src.services.workflow_service.notify_dossier_status_change", new_callable=AsyncMock) as mock_notify,
            patch("src.services.workflow_service._set_dossier_retention_expiry", new_callable=AsyncMock) as mock_retention,
        ):
            from src.services.workflow_service import advance_workflow
            result = await advance_workflow(db, mock_dossier_step, "approved")

        assert result["action"] == "completed"
        assert mock_dossier.status == "completed"
        mock_notify.assert_called_once_with(db, mock_dossier.id, "completed")
        mock_retention.assert_called_once()
