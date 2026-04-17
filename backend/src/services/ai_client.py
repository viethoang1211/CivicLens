import base64
import re

import dashscope
from dashscope import MultiModalConversation

from src.config import settings

dashscope.api_key = settings.dashscope_api_key
if settings.dashscope_api_base:
    dashscope.base_http_api_url = settings.dashscope_api_base


class AIClient:
    OCR_MODEL = "qwen-vl-ocr"
    OCR_FALLBACK_MODEL = "qwen-vl-max"
    CLASSIFICATION_MODEL = "qwen-plus"

    def run_ocr(self, image_data: bytes, use_fallback: bool = False) -> dict:
        model = self.OCR_FALLBACK_MODEL if use_fallback else self.OCR_MODEL
        image_b64 = base64.b64encode(image_data).decode("utf-8")
        messages = [
            {
                "role": "user",
                "content": [
                    {"image": f"data:image/jpeg;base64,{image_b64}"},
                    {
                        "text": "Extract all text from this document image. "
                        "Include both printed and handwritten text. Output the raw text only."
                    },
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
        """Text-based classification using OCR content analysis."""
        type_descriptions = "\n".join(
            f"- Code: {dt['code']}, Tên: {dt['name']}, Mô tả: {dt.get('description', '')}"
            for dt in document_types
        )
        prompt = (
            "Bạn là chuyên gia phân loại tài liệu hành chính công Việt Nam.\n"
            "Phân tích nội dung OCR dưới đây và xác định loại tài liệu.\n\n"
            "Hãy suy luận theo các bước:\n"
            "1. Nhận diện từ khóa đặc trưng (tên biểu mẫu, tiêu đề, cơ quan ban hành)\n"
            "2. Nhận diện thông tin cá nhân (họ tên, số CCCD, ngày sinh, địa chỉ)\n"
            "3. So khớp với loại tài liệu phù hợp nhất\n\n"
            f"Các loại tài liệu có thể:\n{type_descriptions}\n\n"
            f"Nội dung OCR:\n{ocr_text[:8000]}\n\n"
            "Trả lời bằng JSON (KHÔNG markdown, KHÔNG giải thích thêm ngoài JSON):\n"
            '{"document_type_code": "...", "confidence": 0.0-1.0, '
            '"reasoning": "giải thích ngắn gọn bằng tiếng Việt tại sao chọn loại này", '
            '"key_signals": ["từ khóa/cụm từ đặc trưng đã phát hiện"], '
            '"alternatives": [{"code": "...", "confidence": 0.0-1.0}]}'
        )

        response = dashscope.Generation.call(
            model=self.CLASSIFICATION_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Bạn là hệ thống phân loại tài liệu hành chính Việt Nam. "
                        "Trả lời bằng JSON hợp lệ duy nhất, không thêm markdown hay giải thích."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            result_format="message",
        )
        if response.status_code != 200:
            raise RuntimeError(f"Classification API error: {response.code} {response.message}")
        return response.output.choices[0].message.content

    def classify_document_visual(self, image_data: bytes, document_types: list[dict]) -> dict:
        """Vision-based classification using visual features (layout, stamps, logos, formatting).

        Uses the multimodal model to classify directly from the document image,
        leveraging classification_prompt hints per document type for visual matching.
        """
        type_descriptions = "\n".join(
            f"- Code: {dt['code']}, Tên: {dt['name']}, "
            f"Đặc điểm nhận dạng: {dt.get('classification_prompt') or dt.get('description', '')}"
            for dt in document_types
        )

        image_b64 = base64.b64encode(image_data).decode("utf-8")

        prompt = (
            "Bạn là chuyên gia phân loại tài liệu hành chính Việt Nam.\n"
            "Hãy NHÌN vào hình ảnh tài liệu này và phân loại dựa trên đặc điểm hình thức.\n\n"
            "Hãy suy luận theo các bước:\n"
            "1. Nhận diện đặc điểm hình thức (bố cục trang, con dấu đỏ, quốc huy, tiêu đề in đậm)\n"
            "2. Nhận diện định dạng (thẻ nhựa, giấy A4, biểu mẫu có ô điền, văn bản tự do)\n"
            "3. Nhận diện nội dung nổi bật (họ tên, số giấy tờ, ngày tháng)\n"
            "4. So khớp với loại tài liệu phù hợp nhất\n\n"
            f"Các loại tài liệu có thể:\n{type_descriptions}\n\n"
            "Trả lời bằng JSON (KHÔNG markdown):\n"
            '{"document_type_code": "...", "confidence": 0.0-1.0, '
            '"reasoning": "giải thích ngắn gọn bằng tiếng Việt", '
            '"visual_features": ["đặc điểm hình thức đã phát hiện"], '
            '"alternatives": [{"code": "...", "confidence": 0.0-1.0}]}'
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

        response = MultiModalConversation.call(
            model=self.OCR_FALLBACK_MODEL,
            messages=messages,
        )
        if response.status_code != 200:
            raise RuntimeError(f"Visual classification API error: {response.code} {response.message}")

        content = response.output.choices[0].message.content
        return content[0]["text"] if isinstance(content, list) else content

    def fill_template(self, ocr_text: str, template_schema: dict) -> dict:
        # Build field list from JSON Schema properties (with titles for better extraction)
        properties = template_schema.get("properties", {}) if isinstance(template_schema, dict) else {}
        if properties:
            field_descriptions = []
            for key, spec in properties.items():
                title = spec.get("title", key) if isinstance(spec, dict) else key
                field_descriptions.append(f"- {key}: {title}")
            fields_text = "\n".join(field_descriptions)
        else:
            # Fallback: treat schema as flat key list
            fields_text = ", ".join(
                k for k in (template_schema.keys() if isinstance(template_schema, dict) else [])
                if not k.startswith("_") and k not in ("type", "required", "properties", "$schema", "$defs")
            )

        prompt = f"""Trích xuất các trường sau từ văn bản tài liệu và trả về dạng JSON.

Các trường cần trích xuất:
{fields_text}

Văn bản tài liệu:
{ocr_text[:8000]}

Trả về một JSON object với tên trường (key) giống chính xác tên ở trên và giá trị được trích xuất. Dùng null cho trường không tìm thấy. CHỈ trả về JSON object, KHÔNG kèm giải thích."""

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
        import base64
        import json as _json

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


    def summarize_document(self, ocr_text: str, document_type_name: str) -> dict:
        """Summarize a document's OCR text with entity extraction.

        Returns: {"summary": str, "key_points": list, "entities": dict}
        """
        import json as _json

        prompt = (
            f"Tóm tắt tài liệu sau trong 2-3 câu ngắn gọn bằng tiếng Việt.\n"
            f"Nêu rõ: (1) loại tài liệu, (2) tên người liên quan, (3) thông tin chính.\n\n"
            f"Ngoài tóm tắt, trích xuất các thực thể chính.\n\n"
            f"Loại tài liệu: {document_type_name}\n"
            f"Nội dung OCR:\n{ocr_text[:8000]}\n\n"
            f'Trả về JSON:\n'
            f'{{\n'
            f'  "summary": "Tóm tắt 2-3 câu",\n'
            f'  "key_points": ["điểm chính 1", "điểm chính 2"],\n'
            f'  "entities": {{\n'
            f'    "persons": ["Tên người 1"],\n'
            f'    "id_numbers": ["012345678901"],\n'
            f'    "dates": ["15/03/1990"],\n'
            f'    "addresses": ["123 Đường ABC, Quận 1, TP.HCM"],\n'
            f'    "amounts": ["1.000.000 VNĐ"]\n'
            f'  }}\n'
            f'}}'
        )

        response = dashscope.Generation.call(
            model=self.CLASSIFICATION_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Bạn là trợ lý hành chính chuyên tóm tắt tài liệu hành chính Việt Nam."
                    "\nTrả lời bằng JSON hợp lệ, KHÔNG thêm markdown.",
                },
                {"role": "user", "content": prompt},
            ],
            result_format="message",
        )
        if response.status_code != 200:
            raise RuntimeError(f"Summarization API error: {response.code} {response.message}")

        raw = response.output.choices[0].message.content
        try:
            cleaned = raw.strip() if isinstance(raw, str) else str(raw)
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
            result = _json.loads(cleaned)
            return {
                "summary": str(result.get("summary", "")),
                "key_points": list(result.get("key_points", [])),
                "entities": result.get("entities", {}),
            }
        except (_json.JSONDecodeError, ValueError):
            return {"summary": "", "key_points": [], "entities": {}}

    def summarize_dossier(self, case_type_name: str, reference_number: str, document_summaries: str) -> dict:
        """Summarize a dossier by aggregating its document summaries.

        Returns: {"summary": str, "key_points": list}
        """
        import json as _json

        prompt = (
            f"Tóm tắt hồ sơ sau trong 2-3 câu ngắn gọn bằng tiếng Việt.\n"
            f"Nêu rõ: (1) mục đích hồ sơ, (2) danh sách tài liệu, (3) thông tin chính.\n\n"
            f"Loại hồ sơ: {case_type_name}\n"
            f"Mã tham chiếu: {reference_number}\n"
            f"Tài liệu đính kèm:\n{document_summaries[:8000]}\n\n"
            f'Trả về JSON:\n'
            f'{{\n'
            f'  "summary": "Tóm tắt 2-3 câu",\n'
            f'  "key_points": ["điểm chính 1", "điểm chính 2"]\n'
            f'}}'
        )

        response = dashscope.Generation.call(
            model=self.CLASSIFICATION_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Bạn là trợ lý hành chính chuyên tóm tắt hồ sơ hành chính Việt Nam."
                    "\nTrả lời bằng JSON hợp lệ, KHÔNG thêm markdown.",
                },
                {"role": "user", "content": prompt},
            ],
            result_format="message",
        )
        if response.status_code != 200:
            raise RuntimeError(f"Dossier summarization API error: {response.code} {response.message}")

        raw = response.output.choices[0].message.content
        try:
            cleaned = raw.strip() if isinstance(raw, str) else str(raw)
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
            result = _json.loads(cleaned)
            return {
                "summary": str(result.get("summary", "")),
                "key_points": list(result.get("key_points", [])),
            }
        except (_json.JSONDecodeError, ValueError):
            return {"summary": "", "key_points": []}


ai_client = AIClient()


# Vietnamese diacritics pattern: letters with diacritical marks common in Vietnamese
_VIETNAMESE_PATTERN = re.compile(
    r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡ"
    r"ùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨ"
    r"ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]"
)

# Structural patterns: dates, numbers, IDs common in Vietnamese government docs
_DATE_PATTERN = re.compile(r"\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}")
_NUMBER_PATTERN = re.compile(r"\d{6,}")  # 6+ digit sequences (CCCD, phone, etc.)


def estimate_ocr_confidence(text: str) -> float:
    """Estimate OCR output quality based on text characteristics.

    Returns a confidence score between 0.0 and 1.0:
    - 0.0: empty or error text
    - 0.2: very short text (< 20 chars), likely garbage
    - 0.3: text with few Vietnamese characters (encoding issues)
    - 0.7: reasonable Vietnamese text
    - 0.85: text with structural patterns (dates, numbers, names)
    """
    if not text or not text.strip():
        return 0.0

    stripped = text.strip()

    # Very short text is likely garbage or partial extraction
    if len(stripped) < 20:
        return 0.2

    # Count Vietnamese diacritical characters
    viet_chars = len(_VIETNAMESE_PATTERN.findall(stripped))
    total_alpha = sum(1 for c in stripped if c.isalpha())

    # If text has alphabetic content but very few Vietnamese characters → encoding issue
    if total_alpha > 10 and viet_chars / max(total_alpha, 1) < 0.05:
        return 0.3

    # Check for structural patterns that indicate a well-extracted document
    has_dates = bool(_DATE_PATTERN.search(stripped))
    has_numbers = bool(_NUMBER_PATTERN.search(stripped))
    has_viet_content = viet_chars >= 5

    if has_dates and has_numbers and has_viet_content:
        return 0.85

    if has_viet_content:
        return 0.7

    # Fallback: some text but not clearly Vietnamese or structured
    return 0.5
