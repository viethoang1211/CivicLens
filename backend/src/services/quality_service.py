from src.config import settings


def assess_image_quality(image_data: bytes) -> dict:
    """Assess scanned document image quality.

    Stable interface contract:
        Input:  image_data (bytes) — raw image bytes (JPEG/PNG)
        Output: dict with keys:
            - "score" (float, 0.0-1.0)   — overall quality score
            - "acceptable" (bool)          — True if score >= settings.image_quality_threshold
            - "guidance" (list[str])       — user-facing tips when quality is low

    Current implementation uses file-size heuristic.
    Production implementation should use PIL/OpenCV for sharpness (Laplacian variance),
    contrast (histogram spread), and skew detection (Hough transform).
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
