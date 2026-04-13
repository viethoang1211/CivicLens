import io
from datetime import datetime, timezone

import oss2

from src.config import settings


class OSSClient:
    def __init__(self):
        auth = oss2.Auth(settings.oss_access_key_id, settings.oss_access_key_secret)
        self.bucket = oss2.Bucket(auth, settings.oss_endpoint, settings.oss_bucket_name)

    def generate_key(self, submission_id: str, page_number: int) -> str:
        now = datetime.now(timezone.utc)
        return f"scans/{now.year}/{now.month:02d}/{now.day:02d}/{submission_id}/page_{page_number:03d}.jpg"

    def upload(self, key: str, data: bytes) -> str:
        self.bucket.put_object(key, data)
        return key

    def get_presigned_url(self, key: str, expires: int = 3600) -> str:
        return self.bucket.sign_url("GET", key, expires)

    def download(self, key: str) -> bytes:
        result = self.bucket.get_object(key)
        return result.read()


def _create_storage_client():
    if settings.storage_backend == "oss":
        return OSSClient()
    from src.services.local_storage import LocalStorageClient
    return LocalStorageClient()


oss_client = _create_storage_client()
