from src.config import settings


def assess_image_quality(image_data: bytes) -> dict:
    """Assess scanned document image quality.

    Basic heuristic: check file size as a proxy for resolution/detail.
    In production, this would use image processing (PIL/OpenCV) for
    sharpness, contrast, and skew detection.
    """
    size_kb = len(image_data) / 1024

    # Very small files are likely corrupt or extremely low quality
    if size_kb < 10:
        return {
            "score": 0.1,
            "acceptable": False,
            "guidance": ["Image file is too small. Please re-scan with higher resolution."],
        }

    # Basic scoring heuristic based on file size
    if size_kb < 50:
        score = 0.3
    elif size_kb < 200:
        score = 0.6
    elif size_kb < 1000:
        score = 0.8
    else:
        score = 0.9

    acceptable = score >= settings.image_quality_threshold
    guidance = []
    if not acceptable:
        guidance = [
            "Ensure adequate lighting",
            "Hold device steady",
            "Avoid shadows on the document",
            "Make sure the document fills the frame",
        ]

    return {"score": score, "acceptable": acceptable, "guidance": guidance}
