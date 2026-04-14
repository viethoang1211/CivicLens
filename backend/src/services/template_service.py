import logging

logger = logging.getLogger(__name__)


def validate_template_data(template_data: dict | None, template_schema: dict) -> dict:
    """Validate and sanitize template data against the document type's schema.

    Returns cleaned template data with only the fields defined in the schema.
    """
    if not template_data:
        return dict.fromkeys(template_schema, None)

    required_fields = template_schema.get("required", []) if isinstance(template_schema.get("required"), list) else []

    cleaned = {}
    for field_name, field_def in template_schema.items():
        if field_name == "required":
            continue
        value = template_data.get(field_name)
        field_type = field_def.get("type", "string") if isinstance(field_def, dict) else "string"

        if value is not None:
            if field_type == "string":
                value = str(value).strip()
            elif field_type in ("number", "float"):
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    value = None
            elif field_type in ("integer", "int"):
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    value = None

        if value is None and field_name in required_fields:
            logger.warning("Required field '%s' is missing or invalid", field_name)

        cleaned[field_name] = value

    return cleaned
