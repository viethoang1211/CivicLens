"""Unit tests for summarization service."""

import uuid
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session


def _make_page(ocr_text="Nguyễn Văn An sinh ngày 15/03/1990", confidence=0.85):
    page = MagicMock()
    page.ocr_corrected_text = None
    page.ocr_raw_text = ocr_text
    page.ocr_confidence = confidence
    page.page_number = 1
    return page


def _make_submission(doc_type_id=None):
    sub = MagicMock()
    sub.id = uuid.uuid4()
    sub.document_type_id = doc_type_id or uuid.uuid4()
    sub.template_data = {}
    sub.ai_summary = None
    sub.ai_summary_generated_at = None
    return sub


def _make_doc_type(name="Giấy khai sinh"):
    dt = MagicMock()
    dt.id = uuid.uuid4()
    dt.name = name
    return dt


class TestGenerateSubmissionSummary:
    """Test generate_submission_summary."""

    @patch("src.services.summarization_service.ai_client")
    def test_generates_summary_with_valid_ocr(self, mock_ai):
        """Valid OCR text should produce a summary and entities."""
        mock_ai.summarize_document.return_value = {
            "summary": "Giấy khai sinh của Nguyễn Văn An",
            "key_points": ["khai sinh", "Nguyễn Văn An"],
            "entities": {
                "persons": ["Nguyễn Văn An"],
                "id_numbers": ["012345678901"],
                "dates": ["15/03/1990"],
                "addresses": [],
                "amounts": [],
            },
        }

        page = _make_page()
        sub = _make_submission()
        dt = _make_doc_type()

        db = MagicMock(spec=Session)
        # Setup execute returns: submission, pages, doc_type
        sub_result = MagicMock()
        sub_result.scalar_one_or_none.return_value = sub
        pages_result = MagicMock()
        pages_result.scalars.return_value.all.return_value = [page]
        dt_result = MagicMock()
        dt_result.scalar_one_or_none.return_value = dt
        db.execute.side_effect = [sub_result, pages_result, dt_result]

        from src.services.summarization_service import generate_submission_summary
        generate_submission_summary(db, sub.id)

        assert sub.ai_summary == "Giấy khai sinh của Nguyễn Văn An"
        assert sub.ai_summary_generated_at is not None
        assert sub.template_data["_entities"]["persons"] == ["Nguyễn Văn An"]
        db.commit.assert_called_once()

    @patch("src.services.summarization_service.ai_client")
    def test_skips_when_ocr_confidence_low(self, mock_ai):
        """OCR confidence < 0.3 should skip summarization."""
        page = _make_page(confidence=0.2)
        sub = _make_submission()

        db = MagicMock(spec=Session)
        sub_result = MagicMock()
        sub_result.scalar_one_or_none.return_value = sub
        pages_result = MagicMock()
        pages_result.scalars.return_value.all.return_value = [page]
        db.execute.side_effect = [sub_result, pages_result]

        from src.services.summarization_service import generate_submission_summary
        generate_submission_summary(db, sub.id)

        mock_ai.summarize_document.assert_not_called()
        assert sub.ai_summary is None

    @patch("src.services.summarization_service.ai_client")
    def test_skips_when_ocr_text_empty(self, mock_ai):
        """Empty OCR text should skip summarization."""
        page = _make_page(ocr_text="", confidence=0.9)
        page.ocr_corrected_text = None
        page.ocr_raw_text = ""

        sub = _make_submission()

        db = MagicMock(spec=Session)
        sub_result = MagicMock()
        sub_result.scalar_one_or_none.return_value = sub
        pages_result = MagicMock()
        pages_result.scalars.return_value.all.return_value = [page]
        db.execute.side_effect = [sub_result, pages_result]

        from src.services.summarization_service import generate_submission_summary
        generate_submission_summary(db, sub.id)

        mock_ai.summarize_document.assert_not_called()

    @patch("src.services.summarization_service.ai_client")
    def test_entity_extraction_stores_in_template_data(self, mock_ai):
        """Entities should be stored under template_data['_entities']."""
        entities = {
            "persons": ["Trần Thị Bình"],
            "id_numbers": ["098765432109"],
            "dates": [],
            "addresses": ["456 Đường XYZ"],
            "amounts": [],
        }
        mock_ai.summarize_document.return_value = {
            "summary": "Test summary",
            "key_points": [],
            "entities": entities,
        }

        page = _make_page()
        sub = _make_submission()
        sub.template_data = {"existing_key": "value"}
        dt = _make_doc_type()

        db = MagicMock(spec=Session)
        sub_result = MagicMock()
        sub_result.scalar_one_or_none.return_value = sub
        pages_result = MagicMock()
        pages_result.scalars.return_value.all.return_value = [page]
        dt_result = MagicMock()
        dt_result.scalar_one_or_none.return_value = dt
        db.execute.side_effect = [sub_result, pages_result, dt_result]

        from src.services.summarization_service import generate_submission_summary
        generate_submission_summary(db, sub.id)

        assert "_entities" in sub.template_data
        assert sub.template_data["_entities"] == entities
        assert sub.template_data["existing_key"] == "value"


class TestGenerateDossierSummary:
    """Test generate_dossier_summary."""

    @patch("src.services.summarization_service.ai_client")
    def test_aggregates_document_summaries(self, mock_ai):
        """Dossier summary should aggregate from document OCR texts."""
        mock_ai.summarize_dossier.return_value = {
            "summary": "Hồ sơ đăng ký khai sinh gồm 2 tài liệu",
            "key_points": ["khai sinh", "2 tài liệu"],
        }

        dossier = MagicMock()
        dossier.id = uuid.uuid4()
        dossier.case_type_id = uuid.uuid4()
        dossier.reference_number = "HS-20260415-001"
        dossier.ai_summary = None
        dossier.ai_summary_generated_at = None

        case_type = MagicMock()
        case_type.name = "Đăng ký khai sinh"

        doc = MagicMock()
        doc.id = uuid.uuid4()

        page = _make_page()

        db = MagicMock(spec=Session)
        dos_result = MagicMock()
        dos_result.scalar_one_or_none.return_value = dossier
        ct_result = MagicMock()
        ct_result.scalar_one_or_none.return_value = case_type
        docs_result = MagicMock()
        docs_result.scalars.return_value.all.return_value = [doc]
        pages_result = MagicMock()
        pages_result.scalars.return_value.all.return_value = [page]
        db.execute.side_effect = [dos_result, ct_result, docs_result, pages_result]

        from src.services.summarization_service import generate_dossier_summary
        generate_dossier_summary(db, dossier.id)

        assert dossier.ai_summary == "Hồ sơ đăng ký khai sinh gồm 2 tài liệu"
        db.commit.assert_called_once()
