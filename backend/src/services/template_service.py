def validate_template_data(template_data: dict | None, template_schema: dict) -> dict:
    """Validate and sanitize template data against the document type's schema.

    Returns cleaned template data with only the fields defined in the schema.
    """
    if not template_data:
        return {key: None for key in template_schema}

    cleaned = {}
    for field_name, field_def in template_schema.items():
        value = template_data.get(field_name)
        cleaned[field_name] = value  # Basic passthrough; real impl would type-check

    return cleaned
