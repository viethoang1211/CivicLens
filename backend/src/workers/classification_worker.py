import json
import logging
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

    so_cccd = submission.template_data.get("so_cccd")
    if not so_cccd or not isinstance(so_cccd, str):
        return

    so_cccd = so_cccd.strip()
    if not so_cccd:
        return

    citizen = db.execute(
        select(Citizen).where(Citizen.id_number == so_cccd)
    ).scalar_one_or_none()

    if citizen is None:
        # Auto-create citizen from extracted data
        ho_ten = submission.template_data.get("ho_ten", "").strip() or f"Công dân {so_cccd}"
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
        ocr_text = ai_client.run_ocr(image_data)
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
        # For multi-page: classify from the LAST page (most likely the main document,
        # not the CCCD which is typically scanned first)
        vision_result = None
        first_page = pages[-1] if len(pages) > 1 else (pages[0] if pages else None)
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
        matched_type = None
        for dt in doc_types:
            if dt.code == classification.get("document_type_code"):
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

            # For multi-page scans: extract CCCD number from combined OCR text so
            # citizen auto-linking still works even though ID doc was excluded from
            # classification candidates.
            if len(pages) > 1 and "so_cccd" not in submission.template_data:
                import re as _re
                cccd_match = _re.search(r"\b(\d{12})\b", combined_text)
                if cccd_match:
                    submission.template_data["so_cccd"] = cccd_match.group(1)
                    logger.info(
                        "Multi-page scan %s: extracted CCCD number %s from OCR for citizen linking",
                        submission_id, cccd_match.group(1)
                    )

        # Auto-link citizen if CCCD number found in template data
        if submission.citizen_id is None:
            _try_auto_link_citizen(submission, db)

        # ── Check if CCCD identification is present ──────────────
        # For quick scan submissions, detect whether the scanned document
        # contains citizen identification (CCCD number) so the app can
        # prompt staff to scan a CCCD if missing.
        has_citizen_id = submission.citizen_id is not None
        if not has_citizen_id and isinstance(submission.template_data, dict):
            so_cccd = submission.template_data.get("so_cccd", "")
            has_citizen_id = bool(so_cccd and str(so_cccd).strip())

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

    Uses dashscope vision model in binary (match/no-match) mode.
    Stores result in DossierDocument.ai_match_result as JSONB.
    """
    doc_uuid = uuid.UUID(dossier_document_id)

    with Session(sync_engine) as db:
        doc = db.execute(
            select(DossierDocument).where(DossierDocument.id == doc_uuid)
        ).scalar_one_or_none()

        if doc is None:
            return  # Document was deleted before task ran

        # Get first page image
        first_page = db.execute(
            select(ScannedPage)
            .where(ScannedPage.dossier_document_id == doc_uuid)
            .order_by(ScannedPage.page_number)
        ).scalars().first()

        if first_page is None:
            return  # No pages uploaded yet

        # Load expected document type prompt
        if doc.document_type_id is None:
            return  # No expected type to validate against

        doc_type = db.execute(
            select(DocumentType).where(DocumentType.id == doc.document_type_id)
        ).scalar_one_or_none()

        if doc_type is None or not doc_type.classification_prompt:
            return

        # Download image from OSS
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

        # Auto-link citizen if this is a CCCD document and the dossier has no citizen
        if doc_type.code == "ID_CCCD" and doc.dossier_id:
            dossier = db.execute(
                select(Dossier).where(Dossier.id == doc.dossier_id)
            ).scalar_one_or_none()
            if dossier and dossier.citizen_id is None:
                _try_auto_link_citizen_from_image(dossier, image_data, doc_type, db)
