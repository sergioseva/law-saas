from __future__ import annotations

from typing import BinaryIO

from django.conf import settings

from .base import FileNotFoundInStorage, Storage


class R2Storage(Storage):
    """
    Cloudflare R2 backend (S3-compatible, no egress fees).

    Uses boto3. Credentials and endpoint come from settings:
      R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ENDPOINT, R2_BUCKET.
    """

    def __init__(self) -> None:
        import boto3
        from botocore.config import Config

        self._bucket = settings.R2_BUCKET
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.R2_ENDPOINT,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name="auto",
            config=Config(signature_version="s3v4"),
        )

    def save(self, key: str, fileobj: BinaryIO, *, content_type: str) -> int:
        # boto3.upload_fileobj streams; size isn't reported. Pre-compute by
        # tell()/seek() if the file supports it; otherwise count via wrap.
        size = self._size_or_count(fileobj)
        self._client.upload_fileobj(
            fileobj,
            self._bucket,
            key,
            ExtraArgs={"ContentType": content_type},
        )
        return size

    @staticmethod
    def _size_or_count(fileobj: BinaryIO) -> int:
        try:
            current = fileobj.tell()
            fileobj.seek(0, 2)  # SEEK_END
            end = fileobj.tell()
            fileobj.seek(current)
            return end - current
        except (OSError, AttributeError):
            return 0  # caller can populate from request metadata

    def open(self, key: str) -> BinaryIO:
        from botocore.exceptions import ClientError

        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in {"NoSuchKey", "404"}:
                raise FileNotFoundInStorage(key) from exc
            raise
        return response["Body"]

    def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)

    def exists(self, key: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in {"404", "NoSuchKey"}:
                return False
            raise


__all__ = ["R2Storage"]
