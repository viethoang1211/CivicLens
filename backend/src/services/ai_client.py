import base64

import dashscope
from dashscope import MultiModalConversation

from src.config import settings

dashscope.api_key = settings.dashscope_api_key


class AIClient:
    OCR_MODEL = "qwen-vl-ocr"
    OCR_FALLBACK_MODEL = "qwen3-vl-plus"
    CLASSIFICATION_MODEL = "qwen3.5-flash"

    def run_ocr(self, image_data: bytes, use_fallback: bool = False) -> dict:
        model = self.OCR_FALLBACK_MODEL if use_fallback else self.OCR_MODEL
        image_b64 = base64.b64encode(image_data).decode("utf-8")
        messages = [
            {
                "role": "user",
                "content": [
                    {"image": f"data:image/jpeg;base64,{image_b64}"},
                    {"text": "Extract all text from this document image. Include both printed and handwritten text. Output the raw text only."},
                ],
            }
        ]
        response = MultiModalConversation.call(model=model, messages=messages)
        if response.status_code != 200:
            raise RuntimeError(f"OCR API error: {response.code} {response.message}")
        content = response.output.choices[0].message.content
        text = content[0]["text"] if isinstance(content, list) else content
        return {"text": text, "model": model}

    def classify_document(self, ocr_text: str, document_types: list[dict]) -> dict:
        type_descriptions = "\n".join(
            f"- Code: {dt['code']}, Name: {dt['name']}, Description: {dt.get('description', '')}"
            for dt in document_types
        )
        prompt = f"""Classify the following document text into one of these document types.

Available types:
{type_descriptions}

Document text:
{ocr_text[:8000]}

Respond in JSON format:
{{"document_type_code": "...", "confidence": 0.0-1.0, "alternatives": [{{"code": "...", "confidence": 0.0-1.0}}]}}"""

        response = dashscope.Generation.call(
            model=self.CLASSIFICATION_MODEL,
            messages=[{"role": "user", "content": prompt}],
            result_format="message",
        )
        if response.status_code != 200:
            raise RuntimeError(f"Classification API error: {response.code} {response.message}")
        return response.output.choices[0].message.content

    def fill_template(self, ocr_text: str, template_schema: dict) -> dict:
        fields = ", ".join(template_schema.keys()) if isinstance(template_schema, dict) else str(template_schema)
        prompt = f"""Extract the following fields from the document text and return as JSON.

Fields to extract: {fields}

Document text:
{ocr_text[:8000]}

Return a JSON object with the field names as keys and extracted values. Use null for fields not found."""

        response = dashscope.Generation.call(
            model=self.CLASSIFICATION_MODEL,
            messages=[{"role": "user", "content": prompt}],
            result_format="message",
        )
        if response.status_code != 200:
            raise RuntimeError(f"Template fill API error: {response.code} {response.message}")
        return response.output.choices[0].message.content

    def validate_document_slot(self, image_data: bytes, document_type_prompt: str) -> dict:
        """Binary slot validation: does this image match the expected document type?

        Returns: {"match": bool, "confidence": float, "reason": str}
        """
        import base64, json as _json

        image_b64 = base64.b64encode(image_data).decode("utf-8")
        prompt = (
            f"Does this image show a document matching the following description?\n"
            f"Description: {document_type_prompt}\n\n"
            f"Respond ONLY with valid JSON in this exact format:\n"
            f'{{ "match": true or false, "confidence": 0.0 to 1.0, "reason": "one sentence explanation" }}'
        )
        messages = [
            {
                "role": "user",
                "content": [
                    {"image": f"data:image/jpeg;base64,{image_b64}"},
                    {"text": prompt},
                ],
            }
        ]
        response = MultiModalConversation.call(model=self.OCR_FALLBACK_MODEL, messages=messages)
        if response.status_code != 200:
            raise RuntimeError(f"Slot validation API error: {response.code} {response.message}")

        content = response.output.choices[0].message.content
        raw = content[0]["text"] if isinstance(content, list) else content

        try:
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
            result = _json.loads(cleaned)
            return {
                "match": bool(result.get("match", False)),
                "confidence": float(result.get("confidence", 0.0)),
                "reason": str(result.get("reason", "")),
            }
        except (ValueError, KeyError, _json.JSONDecodeError):
            return {"match": False, "confidence": 0.0, "reason": "Unable to parse AI response"}


ai_client = AIClient()
