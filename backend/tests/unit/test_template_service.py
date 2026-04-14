"""Unit tests for template_service.validate_template_data."""

from src.services.template_service import validate_template_data


class TestValidateTemplateData:
    def test_none_input_returns_all_none(self):
        schema = {
            "full_name": {"type": "string"},
            "age": {"type": "integer"},
        }
        result = validate_template_data(None, schema)
        assert result == {"full_name": None, "age": None}

    def test_empty_dict_returns_all_none(self):
        schema = {"full_name": {"type": "string"}}
        result = validate_template_data({}, schema)
        assert result == {"full_name": None}

    def test_string_field_strips_whitespace(self):
        schema = {"full_name": {"type": "string"}}
        result = validate_template_data({"full_name": "  Nguyễn Văn An  "}, schema)
        assert result["full_name"] == "Nguyễn Văn An"

    def test_number_field_coerces_from_string(self):
        schema = {"amount": {"type": "number"}}
        result = validate_template_data({"amount": "42.5"}, schema)
        assert result["amount"] == 42.5

    def test_integer_field_coerces_from_string(self):
        schema = {"age": {"type": "integer"}}
        result = validate_template_data({"age": "25"}, schema)
        assert result["age"] == 25

    def test_invalid_number_returns_none(self):
        schema = {"amount": {"type": "number"}}
        result = validate_template_data({"amount": "not-a-number"}, schema)
        assert result["amount"] is None

    def test_invalid_integer_returns_none(self):
        schema = {"age": {"type": "integer"}}
        result = validate_template_data({"age": "abc"}, schema)
        assert result["age"] is None

    def test_missing_required_field_logged(self, caplog):
        schema = {
            "required": ["full_name"],
            "full_name": {"type": "string"},
        }
        result = validate_template_data({"other": "val"}, schema)
        assert result["full_name"] is None
        assert "Required field 'full_name' is missing" in caplog.text

    def test_extra_fields_excluded(self):
        schema = {"full_name": {"type": "string"}}
        result = validate_template_data(
            {"full_name": "An", "extra_field": "should not appear"}, schema
        )
        assert "extra_field" not in result
        assert result == {"full_name": "An"}

    def test_required_key_not_in_output(self):
        schema = {
            "required": ["name"],
            "name": {"type": "string"},
        }
        result = validate_template_data({"name": "test"}, schema)
        assert "required" not in result

    def test_field_def_without_type_defaults_to_string(self):
        schema = {"full_name": {"description": "Name"}}
        result = validate_template_data({"full_name": 123}, schema)
        assert result["full_name"] == "123"

    def test_float_type_alias(self):
        schema = {"score": {"type": "float"}}
        result = validate_template_data({"score": "0.95"}, schema)
        assert result["score"] == 0.95

    def test_int_type_alias(self):
        schema = {"count": {"type": "int"}}
        result = validate_template_data({"count": "7"}, schema)
        assert result["count"] == 7
