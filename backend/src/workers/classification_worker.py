import json
import logging
import re
import uuid

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.config import settings
from src.models.citizen import Citizen
from src.models.document_type import DocumentType
from src.models.dossier import Dossier
from src.models.dossier_document import DossierDocument
from src.models.scanned_page import ScannedPage
from src.models.submission import Submission
from src.services.ai_client import ai_client
from src.workers.celery_app import celery_app

sync_engine = create_engine(settings.database_url)

logger = logging.getLogger(__name__)


# ── JSON parsing helper ──────────────────────────────────────────

def _parse_ai_json(raw_result) -> dict | None:
    """Safely parse AI classification result from raw string or dict."""
    try:
        if isinstance(raw_result, dict):
            return raw_result
        if isinstance(raw_result, str):
            cleaned = raw_result.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(cleaned)
    except (json.JSONDecodeError, IndexError, ValueError):
        return None


# ── Dual-path ensemble ───────────────────────────────────────────

def _ensemble_classification(
    text_result: dict | None,
    vision_result: dict | None,
) -> dict:
    """Combine text-based and vision-based classification into a calibrated result.

    Strategy:
    - Both agree on document type  → average confidence + 10% agreement bonus (capped at 1.0)
    - Disagree → pick highest confidence, apply 20% penalty, include other as alternative
    - One path failed → use the surviving path as-is
    """
    if text_result is None and vision_result is None:
        return {"document_type_code": None, "confidence": 0.0, "method": "failed"}

    if text_result is None:
        vision_result["method"] = "vision_only"
        return vision_result

    if vision_result is None:
        text_result["method"] = "text_only"
        return text_result

    text_code = text_result.get("document_type_code")
    vision_code = vision_result.get("document_type_code")
    text_conf = float(text_result.get("confidence", 0.0))
    vision_conf = float(vision_result.get("confidence", 0.0))

    if text_code == vision_code:
        # ── Both models agree → boost confidence ──
        ensemble_conf = min(1.0, (text_conf + vision_conf) / 2 + 0.10)

        reasoning_parts = []
        if vision_result.get("reasoning"):
            reasoning_parts.append(f"[Hình ảnh] {vision_result['reasoning']}")
        if text_result.get("reasoning"):
            reasoning_parts.append(f"[Nội dung] {text_result['reasoning']}")

        return {
            "document_type_code": text_code,
            "confidence": round(ensemble_conf, 4),
            "method": "ensemble_agree",
            "reasoning": " | ".join(reasoning_parts) or None,
            "visual_features": vision_result.get("visual_features", []),
            "key_signals": text_result.get("key_signals", []),
            "alternatives": text_result.get("alternatives", []),
            "ensemble_detail": {
                "text_code": text_code,
                "text_confidence": text_conf,
                "vision_code": vision_code,
                "vision_confidence": vision_conf,
                "agreement": True,
            },
        }

    # ── Models disagree → use highest confidence with penalty ──
    if vision_conf >= text_conf:
        primary, secondary, source = vision_result, text_result, "vision"
    else:
        primary, secondary, source = text_result, vision_result, "text"

    primary_conf = float(primary.get("confidence", 0.0))
    ensemble_conf = primary_conf * 0.80  # 20% penalty for disagreement

    # Include the other model's pick as the first alternative
    secondary_alt = {
        "code": secondary.get("document_type_code"),
        "confidence": float(secondary.get("confidence", 0.0)),
    }
    alternatives = [secondary_alt] + primary.get("alternatives", [])

    reasoning_parts = []
    if primary.get("reasoning"):
        reasoning_parts.append(f"[{source}] {primary['reasoning']}")
    if secondary.get("reasoning"):
        other_source = "text" if source == "vision" else "vision"
        reasoning_parts.append(f"[{other_source}] {secondary['reasoning']}")

    return {
        "document_type_code": primary.get("document_type_code"),
        "confidence": round(ensemble_conf, 4),
        "method": "ensemble_disagree",
        "reasoning": " | ".join(reasoning_parts) or None,
        "visual_features": vision_result.get("visual_features", []),
        "key_signals": text_result.get("key_signals", []),
        "alternatives": alternatives[:5],
        "ensemble_detail": {
            "text_code": text_code,
            "text_confidence": text_conf,
            "vision_code": vision_code,
            "vision_confidence": vision_conf,
            "agreement": False,
        },
    }


def _try_auto_link_citizen(submission: Submission, db: Session) -> None:
    """Auto-link citizen to submission (and its dossier) if CCCD number found in template_data."""
    if not isinstance(submission.template_data, dict):
        return

    # Look for CCCD number in order of preference: so_cccd, then any cccd_* field
    so_cccd = submission.template_data.get("so_cccd")
    if not so_cccd or not isinstance(so_cccd, str) or not so_cccd.strip():
        # Try other known CCCD field names (e.g. cccd_me from birth registration form)
        for key in ("cccd_me", "cccd_cha", "id_number"):
            val = submission.template_data.get(key)
            if val and isinstance(val, str) and val.strip():
                so_cccd = val.strip()
                # Mirror into so_cccd for consistent downstream access
                submission.template_data["so_cccd"] = so_cccd
                break

    if not so_cccd or not isinstance(so_cccd, str):
        return

    so_cccd = so_cccd.strip()
    if not so_cccd:
        return

    citizen = db.execute(
        select(Citizen).where(Citizen.id_number == so_cccd)
    ).scalar_one_or_none()

    if citizen is None:
        # Try various name fields in priority order:
        # _cccd_ho_ten = extracted from CCCD page directly (most reliable)
        # ho_ten = CCCD main doc field
        # nguoi_di_dang_ky / ho_ten_me = birth registration form submitter
        ho_ten = (
            submission.template_data.get("_cccd_ho_ten", "").strip()
            or submission.template_data.get("ho_ten", "").strip()
            or submission.template_data.get("nguoi_di_dang_ky", "").strip()
            or submission.template_data.get("ho_ten_me", "").strip()
            or f"Công dân {so_cccd}"
        )
        citizen = Citizen(
            vneid_subject_id=f"auto_{so_cccd}",
            full_name=ho_ten,
            id_number=so_cccd,
        )
        db.add(citizen)
        db.flush()
        logger.info("Auto-created citizen %s (%s) from OCR data", so_cccd, ho_ten)

    submission.citizen_id = citizen.id
    logger.info("Auto-linked submission %s to citizen %s", submission.id, so_cccd)

    # Also link the dossier if it exists and has no citizen
    if submission.dossier_id:
        dossier = db.execute(
            select(Dossier).where(Dossier.id == submission.dossier_id)
        ).scalar_one_or_none()
        if dossier and dossier.citizen_id is None:
            dossier.citizen_id = citizen.id
            logger.info("Auto-linked dossier %s to citizen %s", dossier.id, so_cccd)


def _try_auto_link_citizen_from_image(dossier: Dossier, image_data: bytes, doc_type: DocumentType, db: Session) -> None:
    """Run OCR + template fill on a CCCD image to extract citizen info and auto-link to dossier."""
    try:
        ocr_result = ai_client.run_ocr(image_data)
        ocr_text = ocr_result["text"] if isinstance(ocr_result, dict) else str(ocr_result)
        if not ocr_text or not ocr_text.strip():
            return

        template_result = ai_client.fill_template(ocr_text, doc_type.template_schema)
        if isinstance(template_result, str):
            cleaned = template_result.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
            filled = json.loads(cleaned)
        else:
            filled = template_result

        so_cccd = filled.get("so_cccd", "").strip() if isinstance(filled, dict) else ""
        if not so_cccd:
            return

        citizen = db.execute(
            select(Citizen).where(Citizen.id_number == so_cccd)
        ).scalar_one_or_none()

        if citizen is None:
            ho_ten = filled.get("ho_ten", "").strip() or f"Công dân {so_cccd}"
            citizen = Citizen(
                vneid_subject_id=f"auto_{so_cccd}",
                full_name=ho_ten,
                id_number=so_cccd,
            )
            db.add(citizen)
            db.flush()
            logger.info("Auto-created citizen %s (%s) from CCCD image", so_cccd, ho_ten)

        dossier.citizen_id = citizen.id
        db.commit()
        logger.info("Auto-linked dossier %s to citizen %s from CCCD image", dossier.id, so_cccd)

    except Exception:
        logger.exception("Failed to auto-link citizen from CCCD image for dossier %s", dossier.id)


# ── Smart CCCD detection ─────────────────────────────────────────

# Vietnamese CCCD has distinctive keywords on the card
_CCCD_KEYWORDS = [
    "căn cước công dân",
    "citizen identity card",
    "can cuoc cong dan",
    "số / no",
    "họ và tên / full name",
    "date of birth",
    "giới tính / sex",
    "quốc tịch / nationality",
    "quê quán / place of origin",
    "nơi thường trú / place of residence",
]

# Province codes: 001-096 (valid Vietnamese province codes)
# 4th digit encodes gender + century: 0/1 = male 1900s/2000s, 2/3 = female 1900s/2000s
_CCCD_NUMBER_RE = re.compile(r"\b(0[0-9]{2}[0-3]\d{8})\b")


def _validate_cccd_number(number: str) -> bool:
    """Validate Vietnamese CCCD number format (12 digits with province + gender/century encoding)."""
    if not number or len(number) != 12 or not number.isdigit():
        return False
    province = int(number[:3])
    if province < 1 or province > 96:
        return False
    gender_century = int(number[3])
    if gender_century > 3:
        return False
    return True


def _detect_cccd_page(pages: list[ScannedPage]) -> tuple[ScannedPage | None, str | None]:
    """Detect which page is a CCCD by analyzing OCR text for distinctive keywords.

    Returns (cccd_page, cccd_number) or (None, None) if no CCCD found.
    """
    for page in pages:
        ocr_text = (page.ocr_corrected_text or page.ocr_raw_text or "").lower()
        if not ocr_text.strip():
            continue

        # Count how many CCCD keywords appear in this page's text
        keyword_hits = sum(1 for kw in _CCCD_KEYWORDS if kw in ocr_text)

        if keyword_hits >= 3:
            # This page is almost certainly a CCCD — extract the number
            original_text = page.ocr_corrected_text or page.ocr_raw_text or ""
            matches = _CCCD_NUMBER_RE.findall(original_text)
            for candidate in matches:
                if _validate_cccd_number(candidate):
                    logger.info(
                        "CCCD detected on page %d (keywords=%d, number=%s)",
                        page.page_number, keyword_hits, candidate,
                    )
                    return page, candidate

            # Keywords found but no valid number — still flag as CCCD page
            logger.info("CCCD page detected (keywords=%d) but no valid number extracted", keyword_hits)
            return page, None

    return None, None


@celery_app.task(name="classification.run", bind=True, max_retries=3)
def run_classification(self, submission_id: str):
    """Dual-path ensemble classification: Vision + Text models cross-validate.

    Path 1 (Text):   qwen3.5-flash classifies from OCR text content
    Path 2 (Vision): qwen3-vl-plus classifies from the document image directly
    Ensemble:        Combine both results with calibrated confidence scoring
    """
    sub_uuid = uuid.UUID(submission_id)

    with Session(sync_engine) as db:
        # Gather OCR text from all pages
        pages = db.execute(
            select(ScannedPage)
            .where(ScannedPage.submission_id == sub_uuid)
            .order_by(ScannedPage.page_number)
        ).scalars().all()

        combined_text = "\n\n".join(
            p.ocr_corrected_text or p.ocr_raw_text or "" for p in pages
        )

        if not combined_text.strip():
            return  # Nothing to classify

        # Fetch active document types
        doc_types = db.execute(
            select(DocumentType).where(DocumentType.is_active.is_(True))
        ).scalars().all()

        # ── Exclude identity documents when scanning multiple pages ────
        # CCCD/Passport are used solely for citizen identification.
        # When a submission has >1 page (e.g. CCCD + birth registration form),
        # the main document to classify is NOT the identity document.
        ID_DOC_CODES = {"ID_CCCD", "PASSPORT_VN"}
        if len(pages) > 1:
            classifiable_types = [dt for dt in doc_types if dt.code not in ID_DOC_CODES]
            logger.info(
                "Multi-page submission %s (%d pages): excluding ID docs from classification candidates",
                submission_id, len(pages)
            )
        else:
            classifiable_types = doc_types

        # ── Path 1: Text-based classification ────────────────────
        text_result = None
        try:
            type_dicts = [
                {"code": dt.code, "name": dt.name, "description": dt.description or ""}
                for dt in classifiable_types
            ]
            raw_text = ai_client.classify_document(combined_text, type_dicts)
            text_result = _parse_ai_json(raw_text)
            logger.info("Text classification for %s: %s (%.2f)",
                        submission_id,
                        text_result.get("document_type_code") if text_result else "FAILED",
                        float(text_result.get("confidence", 0)) if text_result else 0)
        except Exception:
            logger.exception("Text classification failed for %s", submission_id)

        # ── Path 2: Vision-based classification ──────────────────
        # For multi-page: skip the CCCD page and use the main document page.
        # Use _detect_cccd_page to find which page is the ID card, then pick any other page.
        vision_result = None
        if len(pages) > 1:
            cccd_page, _ = _detect_cccd_page(pages)
            non_cccd_pages = [p for p in pages if cccd_page is None or p.id != cccd_page.id]
            vision_page = non_cccd_pages[0] if non_cccd_pages else pages[-1]
            logger.info(
                "Multi-page %s: using page %d for vision (CCCD page: %s)",
                submission_id, vision_page.page_number,
                cccd_page.page_number if cccd_page else "not detected",
            )
        else:
            vision_page = pages[0] if pages else None
        first_page = vision_page
        if first_page and first_page.image_oss_key:
            try:
                from src.services.oss_client import oss_client
                image_data = oss_client.download(first_page.image_oss_key)

                # Pass classification_prompt as visual hints
                vision_type_dicts = [
                    {
                        "code": dt.code,
                        "name": dt.name,
                        "classification_prompt": dt.classification_prompt or dt.description or "",
                    }
                    for dt in classifiable_types
                ]
                raw_vision = ai_client.classify_document_visual(image_data, vision_type_dicts)
                vision_result = _parse_ai_json(raw_vision)
                logger.info("Vision classification for %s: %s (%.2f)",
                            submission_id,
                            vision_result.get("document_type_code") if vision_result else "FAILED",
                            float(vision_result.get("confidence", 0)) if vision_result else 0)
            except Exception:
                logger.exception("Vision classification failed for %s", submission_id)

        # ── Ensemble: combine both paths ─────────────────────────
        classification = _ensemble_classification(text_result, vision_result)
        logger.info("Ensemble result for %s: %s (%.2f, method=%s)",
                     submission_id,
                     classification.get("document_type_code"),
                     float(classification.get("confidence", 0)),
                     classification.get("method"))

        if classification.get("document_type_code") is None:
            return  # Both paths failed; leave in pending_classification

        # Match document type by code
        valid_codes = {dt.code for dt in doc_types}
        matched_type = None
        for dt in doc_types:
            if dt.code == classification.get("document_type_code"):
                matched_type = dt
                break

        # Fallback: if ensemble result code not in DB (AI hallucinated a code),
        # try the text-only result which is more constrained to valid codes.
        if matched_type is None and text_result:
            text_code = text_result.get("document_type_code")
            if text_code and text_code in valid_codes:
                logger.warning(
                    "Ensemble code '%s' not in DB for %s — falling back to text result '%s'",
                    classification.get("document_type_code"), submission_id, text_code,
                )
                classification = text_result
                classification["method"] = "text_only_fallback"
                for dt in doc_types:
                    if dt.code == text_code:
                        matched_type = dt
                        break

        submission = db.execute(select(Submission).where(Submission.id == sub_uuid)).scalar_one()

        if matched_type:
            submission.document_type_id = matched_type.id
            confidence = classification.get("confidence", 0.0)
            submission.classification_confidence = confidence

            # Enforce confidence threshold
            if confidence >= settings.classification_confidence_threshold:
                submission.classification_method = "ai"
            else:
                submission.classification_method = "ai_low_confidence"

            # Prepare template_data with classification metadata
            if submission.template_data is None:
                submission.template_data = {}

            # Store alternatives for staff review
            alternatives = classification.get("alternatives", [])
            if alternatives:
                submission.template_data["_classification_alternatives"] = alternatives

            # Store ensemble reasoning & details for audit trail
            submission.template_data["_classification_reasoning"] = classification.get("reasoning")
            submission.template_data["_classification_method"] = classification.get("method")
            submission.template_data["_classification_visual_features"] = classification.get("visual_features", [])
            submission.template_data["_classification_key_signals"] = classification.get("key_signals", [])
            submission.template_data["_classification_ensemble"] = classification.get("ensemble_detail")

            # Run template filling
            template_result = ai_client.fill_template(combined_text, matched_type.template_schema)
            try:
                if isinstance(template_result, str):
                    cleaned = template_result.strip()
                    if cleaned.startswith("```"):
                        cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
                    filled = json.loads(cleaned)
                else:
                    filled = template_result
            except (json.JSONDecodeError, IndexError):
                filled = {}

            # Merge template data, preserving classification metadata
            classification_meta = {
                k: v for k, v in submission.template_data.items()
                if k.startswith("_classification_")
            }
            submission.template_data = filled if isinstance(filled, dict) else {}
            submission.template_data.update(classification_meta)

            # For multi-page scans: if a CCCD page is detected, run fill_template
            # with the ID_CCCD schema on that page's OCR text to extract full citizen data
            # (so_cccd, ho_ten, ngay_sinh, etc.) — not just a regex-matched number.
            if len(pages) > 1 and "so_cccd" not in submission.template_data:
                cccd_page, _ = _detect_cccd_page(pages)
                if cccd_page:
                    try:
                        cccd_doc_type = db.execute(
                            select(DocumentType).where(DocumentType.code == "ID_CCCD")
                        ).scalar_one_or_none()
                        if cccd_doc_type and cccd_doc_type.template_schema:
                            cccd_ocr = cccd_page.ocr_corrected_text or cccd_page.ocr_raw_text or ""
                            cccd_raw = ai_client.fill_template(cccd_ocr, cccd_doc_type.template_schema)
                            if isinstance(cccd_raw, str):
                                cleaned = cccd_raw.strip()
                                if cleaned.startswith("```"):
                                    cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
                                cccd_filled = json.loads(cleaned)
                            else:
                                cccd_filled = cccd_raw
                            if isinstance(cccd_filled, dict):
                                # Merge CCCD fields: so_cccd is the primary key, ho_ten etc. as context
                                for key in ("so_cccd", "ho_ten", "ngay_sinh", "gioi_tinh", "que_quan", "noi_thuong_tru"):
                                    val = cccd_filled.get(key)
                                    if val and str(val).strip():
                                        submission.template_data[f"_cccd_{key}"] = str(val).strip()
                                # Promote so_cccd to top-level for citizen linking
                                so_cccd_val = cccd_filled.get("so_cccd", "").strip() if isinstance(cccd_filled.get("so_cccd"), str) else ""
                                if so_cccd_val and _validate_cccd_number(so_cccd_val):
                                    submission.template_data["so_cccd"] = so_cccd_val
                                    logger.info(
                                        "Multi-page scan %s: CCCD data extracted via fill_template (so_cccd=%s, ho_ten=%s)",
                                        submission_id, so_cccd_val, cccd_filled.get("ho_ten", ""),
                                    )
                    except Exception:
                        logger.exception("Failed to fill CCCD template for page %d of submission %s",
                                         cccd_page.page_number, submission_id)

        # Auto-link citizen if CCCD number found in template data
        if submission.citizen_id is None:
            _try_auto_link_citizen(submission, db)

        # ── Check if CCCD identification is present ──────────────
        # For quick scan submissions, detect whether the scanned document
        # contains citizen identification (CCCD number) so the app can
        # prompt staff to scan a CCCD if missing.
        has_citizen_id = submission.citizen_id is not None
        if not has_citizen_id and isinstance(submission.template_data, dict):
            # Check so_cccd or any cccd_* field
            for cccd_key in ("so_cccd", "cccd_me", "cccd_cha", "id_number"):
                val = submission.template_data.get(cccd_key, "")
                if val and str(val).strip():
                    has_citizen_id = True
                    break

        doc_code = matched_type.code if matched_type else None
        is_id_document = doc_code in ("ID_CCCD", "PASSPORT_VN")
        # In a multi-page scan the ID doc was used for citizen data, not as main classification.
        # Treat it as "identified" even though the classified type is not an ID doc.
        if len(pages) > 1:
            is_id_document = False  # Never flag multi-page result as "the ID doc itself"

        if submission.template_data is None:
            submission.template_data = {}

        submission.template_data["_citizen_identified"] = has_citizen_id
        submission.template_data["_is_id_document"] = is_id_document
        if not has_citizen_id and not is_id_document:
            submission.template_data["_missing_cccd_warning"] = (
                "Không tìm thấy thông tin CCCD công dân trong tài liệu. "
                "Vui lòng quét thêm ảnh CCCD/CMND để liên kết hồ sơ với công dân."
            )
        else:
            submission.template_data.pop("_missing_cccd_warning", None)

        submission.status = "pending_classification"  # Stays pending until staff confirms
        db.commit()

    # Chain to summarization after successful classification
    try:
        from src.workers.summarization_worker import generate_summary
        generate_summary.delay(submission_id)
    except Exception:
        logging.getLogger(__name__).exception("Summarization enqueue failed")


@celery_app.task(name="classification.validate_slot", bind=True, max_retries=3)
def validate_document_slot(self, dossier_document_id: str):
    """Validate whether a DossierDocument matches its expected slot's document type.

    Flow:
    1. Run OCR on all pages (if not already done) and store text — same as quick scan
    2. Detect CCCD page via keyword matching on OCR text
    3. If CCCD page found → fill_template with ID_CCCD schema → link citizen to dossier
    4. Validate the slot using vision AI on first page image

    This mirrors the quick-scan flow: citizen linking happens via stored OCR text,
    independent of whether the slot type is ID_CCCD.
    """
    doc_uuid = uuid.UUID(dossier_document_id)

    with Session(sync_engine) as db:
        doc = db.execute(
            select(DossierDocument).where(DossierDocument.id == doc_uuid)
        ).scalar_one_or_none()

        if doc is None:
            return  # Document was deleted before task ran

        # Get ALL pages for this document (ordered)
        all_pages = db.execute(
            select(ScannedPage)
            .where(ScannedPage.dossier_document_id == doc_uuid)
            .order_by(ScannedPage.page_number)
        ).scalars().all()

        if not all_pages:
            return  # No pages uploaded yet

        first_page = all_pages[0]

        # ── Step 1: Load expected document type (slot is pre-typed in dossier) ─
        # We need doc_type early to decide whether to run citizen linking.
        _early_doc_type = None
        if doc.document_type_id:
            _early_doc_type = db.execute(
                select(DocumentType).where(DocumentType.id == doc.document_type_id)
            ).scalar_one_or_none()

        # ── Step 2: OCR all pages + citizen linking for CCCD slots ───────────
        # Dossier pages are not pre-OCR'd. Run OCR now to store text for
        # search indexing. If this slot is ID_CCCD, also extract citizen data.
        try:
            from src.services.oss_client import oss_client as _oss
            for page in all_pages:
                if not page.ocr_raw_text:
                    try:
                        img = _oss.download(page.image_oss_key)
                        ocr_result = ai_client.run_ocr(img)
                        ocr_text = ocr_result["text"] if isinstance(ocr_result, dict) else str(ocr_result)
                        page.ocr_raw_text = ocr_text
                        page.ocr_corrected_text = ocr_text
                    except Exception:
                        logger.warning("OCR failed for page %d of dossier doc %s", page.page_number, doc_uuid)
            db.commit()
        except Exception:
            logger.exception("OCR pre-run failed for dossier doc %s", doc_uuid)

        # Citizen linking: only when this slot is explicitly for CCCD/ID docs.
        # The slot's document_type already tells us this — no keyword detection needed.
        is_id_slot = _early_doc_type and _early_doc_type.code in ("ID_CCCD", "PASSPORT_VN")
        if is_id_slot and doc.dossier_id:
            dossier = db.execute(
                select(Dossier).where(Dossier.id == doc.dossier_id)
            ).scalar_one_or_none()
            if dossier and dossier.citizen_id is None and _early_doc_type.template_schema:
                try:
                    combined_ocr = "\n".join(
                        p.ocr_corrected_text or p.ocr_raw_text or ""
                        for p in all_pages
                    )
                    cccd_raw = ai_client.fill_template(combined_ocr, _early_doc_type.template_schema)
                    if isinstance(cccd_raw, str):
                        cleaned = cccd_raw.strip()
                        if cleaned.startswith("```"):
                            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
                        cccd_filled = json.loads(cleaned)
                    else:
                        cccd_filled = cccd_raw
                    if isinstance(cccd_filled, dict):
                        so_cccd = cccd_filled.get("so_cccd", "").strip() if isinstance(cccd_filled.get("so_cccd"), str) else ""
                        if so_cccd and _validate_cccd_number(so_cccd):
                            ho_ten = cccd_filled.get("ho_ten", "").strip() or f"Công dân {so_cccd}"
                            citizen = db.execute(
                                select(Citizen).where(Citizen.id_number == so_cccd)
                            ).scalar_one_or_none()
                            if citizen is None:
                                citizen = Citizen(
                                    vneid_subject_id=f"auto_{so_cccd}",
                                    full_name=ho_ten,
                                    id_number=so_cccd,
                                )
                                db.add(citizen)
                                db.flush()
                                logger.info("Dossier %s: auto-created citizen %s (%s)", dossier.id, so_cccd, ho_ten)
                            dossier.citizen_id = citizen.id
                            db.commit()
                            logger.info("Dossier %s: auto-linked to citizen %s via ID slot OCR", dossier.id, so_cccd)
                except Exception:
                    logger.exception("Failed citizen linking for ID slot %s of dossier %s", doc_uuid, doc.dossier_id)

        # ── Step 3: Slot validation via vision AI ────────────────────────────
        doc_type = _early_doc_type
        if doc_type is None or not doc_type.classification_prompt:
            return  # No expected type or prompt to validate against

        # Download first page image for vision validation
        try:
            from src.services.oss_client import oss_client as _oss
            image_data = _oss.download(first_page.image_oss_key)
        except Exception:
            return  # OSS unavailable; leave ai_match_result as null

        # Call AI for slot validation
        try:
            match_result = ai_client.validate_document_slot(image_data, doc_type.classification_prompt)
        except Exception as exc:
            raise self.retry(exc=exc, countdown=30) from exc

        doc.ai_match_result = match_result
        db.commit()
