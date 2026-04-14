"""Unit tests for estimate_ocr_confidence heuristic."""

from src.services.ai_client import estimate_ocr_confidence


def test_empty_string_returns_zero():
    assert estimate_ocr_confidence("") == 0.0


def test_none_returns_zero():
    assert estimate_ocr_confidence(None) == 0.0


def test_whitespace_only_returns_zero():
    assert estimate_ocr_confidence("   \n\t  ") == 0.0


def test_short_garbage_returns_low():
    assert estimate_ocr_confidence("abc123") == 0.2


def test_short_text_under_20_chars():
    assert estimate_ocr_confidence("xin chào") == 0.2


def test_non_vietnamese_text_returns_03():
    text = "This is a long English text that has no Vietnamese diacritical characters at all and is over twenty characters"
    assert estimate_ocr_confidence(text) == 0.3


def test_vietnamese_government_text_returns_07_or_higher():
    text = "Nguyễn Văn An sinh ngày tại thành phố Hồ Chí Minh, thường trú tại quận Bình Thạnh"
    result = estimate_ocr_confidence(text)
    assert result >= 0.7


def test_text_with_dates_and_numbers_returns_085():
    text = "Nguyễn Văn An sinh ngày 15/03/1990 tại Hà Nội, số CCCD 012345678901"
    assert estimate_ocr_confidence(text) == 0.85


def test_vietnamese_without_structural_patterns():
    text = "Cộng hòa xã hội chủ nghĩa Việt Nam, Độc lập Tự do Hạnh phúc, kính gửi ông bà"
    result = estimate_ocr_confidence(text)
    assert result == 0.7


def test_text_with_only_dates_no_numbers():
    text = "Nguyễn Văn An sinh ngày 15/03/1990 tại thành phố Hồ Chí Minh thường trú"
    result = estimate_ocr_confidence(text)
    # Has dates + Vietnamese but no 6+ digit number → 0.7
    assert result >= 0.7


def test_non_alpha_text_returns_fallback():
    text = "123 456 789 012 345 678 901 234 567"
    result = estimate_ocr_confidence(text)
    assert result == 0.5
