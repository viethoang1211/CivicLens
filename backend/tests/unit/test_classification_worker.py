"""Unit tests for classification worker confidence threshold enforcement."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session


@pytest.fixture
def mock_db_objects():
    """Create mock database objects for testing."""
    page = MagicMock()
    page.ocr_corrected_text = None
    page.ocr_raw_text = "Nguyễn Văn An sinh ngày 15/03/1990 tại Hà Nội"
    page.page_number = 1

    doc_type = MagicMock()
    doc_type.code = "BIRTH_REG_FORM"
    doc_type.name = "Tờ khai đăng ký khai sinh"
    doc_type.description = "Mẫu đăng ký khai sinh"
    doc_type.id = uuid.uuid4()
    doc_type.is_active = True
    doc_type.template_schema = {"full_name": {"type": "string"}}

    submission = MagicMock()
    submission.id = uuid.uuid4()
    submission.template_data = None

    return page, doc_type, submission


def _setup_session_mock(mock_session, pages, doc_types, submission):
    """Setup mock session execute side effects."""
    pages_result = MagicMock()
    pages_result.scalars.return_value.all.return_value = pages

    types_result = MagicMock()
    types_result.scalars.return_value.all.return_value = doc_types

    sub_result = MagicMock()
    sub_result.scalar_one.return_value = submission

    mock_session.execute.side_effect = [pages_result, types_result, sub_result]


class TestClassificationConfidenceThreshold:
    """Test that classification_method reflects confidence vs threshold."""

    @patch("src.workers.classification_worker.ai_client")
    @patch("src.workers.classification_worker.Session")
    def test_high_confidence_sets_ai_method(self, mock_session_cls, mock_ai, mock_db_objects):
        page, doc_type, submission = mock_db_objects
        sub_id = str(submission.id)

        mock_session = MagicMock(spec=Session)
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        _setup_session_mock(mock_session, [page], [doc_type], submission)

        # AI returns high confidence (0.9 > 0.7 threshold)
        mock_ai.classify_document.return_value = {
            "document_type_code": "BIRTH_REG_FORM",
            "confidence": 0.9,
        }
        mock_ai.fill_template.return_value = {"full_name": "Nguyễn Văn An"}

        from src.workers.classification_worker import run_classification
        run_classification.run(sub_id)

        assert submission.classification_method == "ai"
        assert submission.classification_confidence == 0.9

    @patch("src.workers.classification_worker.ai_client")
    @patch("src.workers.classification_worker.Session")
    def test_low_confidence_sets_ai_low_confidence_method(self, mock_session_cls, mock_ai, mock_db_objects):
        page, doc_type, submission = mock_db_objects
        sub_id = str(submission.id)

        mock_session = MagicMock(spec=Session)
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        _setup_session_mock(mock_session, [page], [doc_type], submission)

        # AI returns low confidence (0.5 < 0.7 threshold)
        mock_ai.classify_document.return_value = {
            "document_type_code": "BIRTH_REG_FORM",
            "confidence": 0.5,
            "alternatives": [
                {"document_type_code": "BIRTH_CERTIFICATE_MEDICAL", "confidence": 0.3}
            ],
        }
        mock_ai.fill_template.return_value = {"full_name": "Nguyễn Văn An"}

        from src.workers.classification_worker import run_classification
        run_classification.run(sub_id)

        assert submission.classification_method == "ai_low_confidence"
        assert submission.classification_confidence == 0.5
        assert submission.template_data["_classification_alternatives"] == [
            {"document_type_code": "BIRTH_CERTIFICATE_MEDICAL", "confidence": 0.3}
        ]

    @patch("src.workers.classification_worker.ai_client")
    @patch("src.workers.classification_worker.Session")
    def test_empty_ocr_text_returns_early(self, mock_session_cls, mock_ai):
        sub_id = str(uuid.uuid4())

        page = MagicMock()
        page.ocr_corrected_text = None
        page.ocr_raw_text = ""
        page.page_number = 1

        mock_session = MagicMock(spec=Session)
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        pages_result = MagicMock()
        pages_result.scalars.return_value.all.return_value = [page]
        mock_session.execute.side_effect = [pages_result]

        from src.workers.classification_worker import run_classification
        run_classification.run(sub_id)

        # Should return early without calling classify
        mock_ai.classify_document.assert_not_called()

    @patch("src.workers.classification_worker.ai_client")
    @patch("src.workers.classification_worker.Session")
    def test_zero_confidence_still_stores_classification(self, mock_session_cls, mock_ai, mock_db_objects):
        page, doc_type, submission = mock_db_objects
        sub_id = str(submission.id)

        mock_session = MagicMock(spec=Session)
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        _setup_session_mock(mock_session, [page], [doc_type], submission)

        mock_ai.classify_document.return_value = {
            "document_type_code": "BIRTH_REG_FORM",
            "confidence": 0.0,
        }
        mock_ai.fill_template.return_value = {"full_name": ""}

        from src.workers.classification_worker import run_classification
        run_classification.run(sub_id)

        assert submission.classification_method == "ai_low_confidence"
        assert submission.classification_confidence == 0.0
