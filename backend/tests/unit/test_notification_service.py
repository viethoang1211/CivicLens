"""Unit tests for notification_service dossier notifications."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.notification_service import (
    notify_dossier_step_advanced,
    notify_dossier_status_change,
)


@pytest.fixture
def mock_dossier():
    dossier = MagicMock()
    dossier.id = uuid.uuid4()
    dossier.citizen_id = uuid.uuid4()
    dossier.reference_number = "HS-20250101-00001"
    return dossier


class TestNotifyDossierStepAdvanced:
    @pytest.mark.asyncio
    async def test_creates_notification_with_reference(self, mock_dossier):
        db = AsyncMock()

        with patch("src.services.notification_service.create_notification", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = MagicMock()
            await notify_dossier_step_advanced(db, mock_dossier, "Phòng Tư pháp", 2)

        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["citizen_id"] == mock_dossier.citizen_id
        assert call_kwargs["submission_id"] is None
        assert call_kwargs["notification_type"] == "dossier_step_advanced"
        assert "HS-20250101-00001" in call_kwargs["title"]
        assert "Phòng Tư pháp" in call_kwargs["title"]
        assert "HS-20250101-00001" in call_kwargs["body"]


class TestNotifyDossierStatusChange:
    @pytest.mark.asyncio
    async def test_in_progress_notification(self):
        db = AsyncMock()
        dossier_id = uuid.uuid4()
        citizen_id = uuid.uuid4()

        mock_dossier = MagicMock()
        mock_dossier.reference_number = "HS-20250101-00002"
        mock_dossier.citizen_id = citizen_id

        dossier_result = MagicMock()
        dossier_result.scalar_one_or_none.return_value = mock_dossier
        db.execute.return_value = dossier_result

        with patch("src.services.notification_service.create_notification", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = MagicMock()
            await notify_dossier_status_change(db, dossier_id, "in_progress")

        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["notification_type"] == "dossier_in_progress"
        assert "tiếp nhận" in call_kwargs["title"]

    @pytest.mark.asyncio
    async def test_completed_notification(self):
        db = AsyncMock()
        dossier_id = uuid.uuid4()
        citizen_id = uuid.uuid4()

        mock_dossier = MagicMock()
        mock_dossier.reference_number = "HS-20250101-00003"
        mock_dossier.citizen_id = citizen_id

        dossier_result = MagicMock()
        dossier_result.scalar_one_or_none.return_value = mock_dossier
        db.execute.return_value = dossier_result

        with patch("src.services.notification_service.create_notification", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = MagicMock()
            await notify_dossier_status_change(db, dossier_id, "completed")

        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["notification_type"] == "dossier_completed"
        assert "hoàn thành" in call_kwargs["title"]

    @pytest.mark.asyncio
    async def test_rejected_notification_with_reason(self):
        db = AsyncMock()
        dossier_id = uuid.uuid4()
        citizen_id = uuid.uuid4()

        mock_dossier = MagicMock()
        mock_dossier.reference_number = "HS-20250101-00004"
        mock_dossier.citizen_id = citizen_id

        dossier_result = MagicMock()
        dossier_result.scalar_one_or_none.return_value = mock_dossier
        db.execute.return_value = dossier_result

        with patch("src.services.notification_service.create_notification", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = MagicMock()
            await notify_dossier_status_change(db, dossier_id, "rejected", "Thiếu giấy tờ")

        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["notification_type"] == "dossier_rejected"
        assert "trả lại" in call_kwargs["title"]
        assert "Thiếu giấy tờ" in call_kwargs["body"]
