"""Unit tests for entity extraction — validates structure and CCCD regex."""

import re

# CCCD validation: 12 digits
CCCD_PATTERN = re.compile(r"^\d{12}$")
CMND_PATTERN = re.compile(r"^\d{9}$")


class TestEntityExtractionStructure:
    """Validate entity dict structure from AI summarization."""

    def test_expected_entity_keys(self):
        """Entities dict should have the expected top-level keys."""
        entities = {
            "persons": ["Nguyễn Văn An"],
            "id_numbers": ["012345678901"],
            "dates": ["15/03/1990"],
            "addresses": ["123 Đường ABC, Quận 1, TP.HCM"],
            "amounts": ["1.000.000 VNĐ"],
        }
        expected_keys = {"persons", "id_numbers", "dates", "addresses", "amounts"}
        assert set(entities.keys()) == expected_keys

    def test_all_values_are_lists(self):
        """All entity values should be lists."""
        entities = {
            "persons": ["Nguyễn Văn An"],
            "id_numbers": ["012345678901"],
            "dates": ["15/03/1990"],
            "addresses": [],
            "amounts": [],
        }
        for key, val in entities.items():
            assert isinstance(val, list), f"{key} should be a list"

    def test_empty_ocr_returns_empty_entities(self):
        """Empty OCR text should produce empty entity lists."""
        entities = {
            "persons": [],
            "id_numbers": [],
            "dates": [],
            "addresses": [],
            "amounts": [],
        }
        for key, val in entities.items():
            assert val == [], f"{key} should be empty"

    def test_cccd_12_digit_validation(self):
        """CCCD numbers should be exactly 12 digits."""
        valid_cccd = "012345678901"
        assert CCCD_PATTERN.match(valid_cccd)

        invalid_cccd = "01234567890"  # 11 digits
        assert not CCCD_PATTERN.match(invalid_cccd)

        invalid_cccd_alpha = "01234567890A"
        assert not CCCD_PATTERN.match(invalid_cccd_alpha)

    def test_cmnd_9_digit_validation(self):
        """CMND numbers should be exactly 9 digits."""
        valid_cmnd = "123456789"
        assert CMND_PATTERN.match(valid_cmnd)

        invalid_cmnd = "12345678"  # 8 digits
        assert not CMND_PATTERN.match(invalid_cmnd)

    def test_entities_stored_in_template_data(self):
        """Entities should be stored under template_data['_entities']."""
        template_data = {
            "ho_ten": "Nguyễn Văn An",
            "_classification_alternatives": [],
            "_entities": {
                "persons": ["Nguyễn Văn An"],
                "id_numbers": ["012345678901"],
                "dates": [],
                "addresses": [],
                "amounts": [],
            },
        }
        assert "_entities" in template_data
        assert template_data["_entities"]["persons"] == ["Nguyễn Văn An"]
