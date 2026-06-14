import pprint
from pathlib import Path
from typing import Dict, List, Optional

from storage.minio_client import upload_file, upload_json
from utils.hash_utils import compute_hash_from_file
from utils.logger import (
    log_ingestion_error,
    log_ingestion_start,
    log_ingestion_success,
    setup_logger,
)
from utils.time_utils import build_minio_date_path, get_timestamp_str


BASE_DIR = Path(__file__).resolve().parents[2]
SAMPLE_DATA_DIR = BASE_DIR / "ingestion" / "files" / "sample_data"
LOGS_BUCKET = "raw-logs"

# Mapping extension → (bucket cible, content_type technique)
EXTENSION_TO_BUCKET = {
    ".csv":  ("raw-documents", "csv"),
    ".pdf":  ("raw-documents", "pdf"),
    ".docx": ("raw-documents", "docx"),
    ".doc":  ("raw-documents", "doc"),
    ".xlsx": ("raw-documents", "xlsx"),
    ".json": ("raw-json",      "json"),
}

log = setup_logger("file_loader")


def _build_metadata(file_path: Path, bucket: str, object_path: str, file_type: str) -> Dict:
    return {
        "source_type":         "file",
        "file_type":           file_type,
        "file_name":           file_path.name,
        "file_size_bytes":     file_path.stat().st_size,
        "content_hash":        compute_hash_from_file(str(file_path)),
        "ingestion_timestamp": get_timestamp_str(),
        "bucket":              bucket,
        "object_path":         object_path,
    }


def process_file(file_path: Path, source_name: str = "local_files") -> Optional[Dict]:
    """
    Ingère un fichier (CSV/JSON/PDF/DOC/XLSX) vers MinIO et publie ses métadonnées.

    Le routage bucket/extension est entièrement piloté par la map
    EXTENSION_TO_BUCKET → on évite toute logique métier en dur.
    """
    extension = file_path.suffix.lower()
    if extension not in EXTENSION_TO_BUCKET:
        log.warning(f"[SKIP] extension non supportée | file={file_path.name}")
        return None

    bucket, file_type = EXTENSION_TO_BUCKET[extension]
    date_path = build_minio_date_path(source_name)
    object_path = f"{date_path}/{file_path.name}"

    try:
        log_ingestion_start(log, source=file_path.name, source_type=file_type)
        upload_file(bucket, object_path, str(file_path))
        metadata = _build_metadata(file_path, bucket, object_path, file_type)

        # Pousser le bloc de métadonnées dans raw-logs (traçabilité)
        metadata_object_path = (
            f"{date_path}/metadata_{file_path.stem}_{file_type}.json"
        )
        upload_json(LOGS_BUCKET, metadata_object_path, metadata)

        log_ingestion_success(
            log,
            source=file_path.name,
            object_name=object_path,
            file_hash=metadata["content_hash"],
            size_bytes=metadata["file_size_bytes"],
        )
        return metadata

    except Exception as exc:
        log_ingestion_error(log, source=file_path.name, error=exc, context=str(file_path))
        return None


def run_file_ingestion(
    directory: Path = SAMPLE_DATA_DIR,
    source_name: str = "local_files",
) -> List[Dict]:
    """Point d'entrée utilisé par le DAG Airflow."""
    if not directory.exists():
        log.warning(f"[NO DATA] dossier introuvable : {directory}")
        return []

    results = []
    for file_path in sorted(directory.iterdir()):
        if not file_path.is_file():
            continue
        metadata = process_file(file_path, source_name=source_name)
        if metadata is not None:
            results.append(metadata)
    return results


if __name__ == "__main__":
    output = run_file_ingestion()
    pprint.pprint(output)