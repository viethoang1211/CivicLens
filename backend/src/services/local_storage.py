from datetime import UTC, datetime
from pathlib import Path

from src.config import settings


class LocalStorageClient:
    """Drop-in replacement for OSSClient that stores files on local disk."""

    def __init__(self):
        self.base_dir = Path(settings.local_storage_path)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def generate_key(self, submission_id: str, page_number: int) -> str:
        now = datetime.now(UTC)
        return f"scans/{now.year}/{now.month:02d}/{now.day:02d}/{submission_id}/page_{page_number:03d}.jpg"

    def upload(self, key: str, data: bytes) -> str:
        file_path = self.base_dir / key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(data)
        return key

    def get_presigned_url(self, key: str, expires: int = 3600) -> str:
        return f"/files/{key}"

    def download(self, key: str) -> bytes:
        file_path = self.base_dir / key
        return file_path.read_bytes()

    def delete(self, key: str) -> None:
        file_path = self.base_dir / key
        if file_path.exists():
            file_path.unlink()
