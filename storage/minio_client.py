import io
import json
import os
from typing import Optional

from dotenv import load_dotenv
from minio import Minio

load_dotenv()


_client: Optional[Minio] = None


def get_client() -> Minio:
    """Retourne un client MinIO singleton, configuré via variables d'env."""
    global _client
    if _client is None:
        endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        secure = os.getenv("MINIO_SECURE", "false").lower() == "true"

        _client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
    return _client


def create_bucket(bucket_name: str) -> bool:
    """Crée le bucket s'il n'existe pas. Retourne True si effectivement créé."""
    client = get_client()
    if client.bucket_exists(bucket_name):
        return False
    client.make_bucket(bucket_name)
    return True


def upload_file(bucket_name: str, object_name: str, file_path: str) -> None:
    """Upload un fichier du disque vers MinIO."""
    client = get_client()
    client.fput_object(bucket_name, object_name, file_path)


def upload_bytes(
    bucket_name: str,
    object_name: str,
    data: bytes,
    content_type: str = "application/octet-stream",
) -> None:
    """Upload un payload binaire (bytes) directement, sans passer par le disque."""
    client = get_client()
    stream = io.BytesIO(data)
    client.put_object(
        bucket_name=bucket_name,
        object_name=object_name,
        data=stream,
        length=len(data),
        content_type=content_type,
    )


def upload_html(bucket_name: str, object_name: str, html: str) -> None:
    """Upload une chaîne HTML directement (encodage UTF-8)."""
    upload_bytes(
        bucket_name=bucket_name,
        object_name=object_name,
        data=html.encode("utf-8"),
        content_type="text/html; charset=utf-8",
    )


def upload_json(bucket_name: str, object_name: str, payload: object) -> None:
    """Sérialise un objet Python en JSON et l'upload."""
    body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    upload_bytes(
        bucket_name=bucket_name,
        object_name=object_name,
        data=body,
        content_type="application/json; charset=utf-8",
    )


def download_file(bucket_name: str, object_name: str, file_path: str) -> str:
    """Télécharge un objet de MinIO vers un fichier local. Retourne le chemin."""
    client = get_client()
    client.fget_object(bucket_name, object_name, file_path)
    return file_path


# Compat : certains modules historiques importaient `client` directement.
client = get_client()