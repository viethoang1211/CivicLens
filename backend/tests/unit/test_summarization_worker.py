"""Unit tests for summarization worker."""

import uuid
from unittest.mock import MagicMock, patch


class TestSummarizationWorker:
    """Test summarization Celery tasks."""

    @patch("src.workers.summarization_worker.Session")
    @patch("src.services.summarization_service.generate_submission_summary")
    def test_generate_summary_calls_service(self, mock_gen, mock_session_cls):
        """generate_summary task should call generate_submission_summary."""
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        from src.workers.summarization_worker import generate_summary

        sub_id = str(uuid.uuid4())
        generate_summary(sub_id)

        mock_gen.assert_called_once()

    @patch("src.workers.summarization_worker.Session")
    @patch("src.services.summarization_service.generate_dossier_summary")
    def test_generate_dossier_summary_calls_service(self, mock_gen, mock_session_cls):
        """generate_dossier_summary task should call the dossier service function."""
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        from src.workers.summarization_worker import generate_dossier_summary

        dos_id = str(uuid.uuid4())
        generate_dossier_summary(dos_id)

        mock_gen.assert_called_once()

    @patch("src.workers.summarization_worker.Session")
    @patch("src.services.summarization_service.generate_submission_summary")
    def test_non_retryable_failure_clears_summary(self, mock_gen, mock_session_cls):
        """Non-retryable exception should set ai_summary to None."""
        mock_gen.side_effect = ValueError("Unexpected error")

        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        # Mock the fallback query in the except block
        mock_sub = MagicMock()
        fallback_result = MagicMock()
        fallback_result.scalar_one_or_none.return_value = mock_sub
        mock_session.execute.return_value = fallback_result

        from src.workers.summarization_worker import generate_summary

        sub_id = str(uuid.uuid4())
        generate_summary(sub_id)

        assert mock_sub.ai_summary is None
