"""MinIO storage client — singleton wrapping the sync `minio` library.

All I/O is wrapped in asyncio.to_thread so endpoints can stay async. MinIO
ships no async client; a threadpool call is lighter than pulling in
aioboto3.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from dataclasses import dataclass
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: Minio | None = None


def _get_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
    return _client


async def ensure_bucket() -> None:
    """Create the evidence bucket on first use. Safe to call repeatedly."""
    client = _get_client()

    def _ensure() -> None:
        if not client.bucket_exists(settings.MINIO_BUCKET):
            client.make_bucket(settings.MINIO_BUCKET)
            logger.info("Created MinIO bucket: %s", settings.MINIO_BUCKET)

    await asyncio.to_thread(_ensure)


@dataclass
class UploadResult:
    storage_key: str
    sha256: str
    size_bytes: int


async def upload_bytes(
    *,
    data: bytes,
    content_type: str,
    prefix: str = "evidence",
) -> UploadResult:
    """Upload bytes, keyed by sha256 for automatic deduplication.

    Reading the full payload into memory is fine at our 100 MB cap and lets
    us hash + size in one pass without a temp file.
    """
    client = _get_client()
    digest = hashlib.sha256(data).hexdigest()
    # Two-level prefix keeps MinIO listings sane once we have thousands of
    # objects — the flat bucket root would become a hot spot otherwise.
    storage_key = f"{prefix}/{digest[:2]}/{digest}"

    from io import BytesIO

    def _put() -> None:
        client.put_object(
            settings.MINIO_BUCKET,
            storage_key,
            BytesIO(data),
            length=len(data),
            content_type=content_type,
        )

    await asyncio.to_thread(_put)
    return UploadResult(storage_key=storage_key, sha256=digest, size_bytes=len(data))


async def get_object_bytes(storage_key: str) -> bytes:
    """Fetch raw object bytes. Used by the backend to stream downloads
    through itself — presigned URLs would leak the internal MinIO hostname
    which the browser can't resolve."""
    client = _get_client()

    def _get() -> bytes:
        response = client.get_object(settings.MINIO_BUCKET, storage_key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    return await asyncio.to_thread(_get)


async def delete_object(storage_key: str) -> None:
    client = _get_client()

    def _del() -> None:
        try:
            client.remove_object(settings.MINIO_BUCKET, storage_key)
        except S3Error as exc:
            # NoSuchKey is fine — it means the dedup pointer count hit zero
            # for a file that was already removed by an earlier evidence row.
            if exc.code != "NoSuchKey":
                raise

    await asyncio.to_thread(_del)
