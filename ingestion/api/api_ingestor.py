import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ingestion.api.openalex_connector import OpenAlexConnector
from storage.minio_client import upload_file, upload_json
from utils.hash_utils import compute_hash_from_text
from utils.logger import (
    log_ingestion_error,
    log_ingestion_start,
    log_ingestion_success,
    log_metadata,
    setup_logger,
)


log = setup_logger("api_ingestor")

LOGS_BUCKET = "raw-logs"


class APIIngestor:
    """
    Orchestrates API ingestion from OpenAlex into local raw JSON storage and MinIO.
    """

    def __init__(
        self,
        bucket_name: str,
        local_raw_dir: str = "data/raw",
        source_name: str = "openalex",
        connector: Optional[OpenAlexConnector] = None
    ):
        self.bucket_name = bucket_name
        self.local_raw_dir = Path(local_raw_dir)
        self.source_name = source_name
        self.connector = connector or OpenAlexConnector(source_name=source_name)

    def ingest_publications(self) -> Dict[str, Any]:
        ingestion_timestamp = datetime.now(timezone.utc)
        partition_path = self._build_partition_path(ingestion_timestamp)

        try:
            log_ingestion_start(
                log=log,
                source=self.source_name,
                source_type="api"
            )

            publications = self.connector.fetch_publications()

            raw_json_text = json.dumps(
                publications,
                ensure_ascii=False,
                sort_keys=True
            )

            content_hash = compute_hash_from_text(raw_json_text)

            raw_file_path, metadata_file_path = self._save_raw_payload(
                records=publications,
                partition_path=partition_path,
                ingestion_timestamp=ingestion_timestamp,
                content_hash=content_hash
            )

            source_url = self.connector.api_connector.build_url()

            metadata = self._build_metadata(
                source_url=source_url,
                ingestion_timestamp=ingestion_timestamp,
                content_hash=content_hash,
                record_count=len(publications),
                status="success"
            )

            self._save_metadata(metadata_file_path, metadata)
            log_metadata(log, metadata)

            object_name = self._build_minio_object_name(
                partition_path=partition_path,
                file_name=raw_file_path.name
            )

            upload_file(
                bucket_name=self.bucket_name,
                object_name=object_name,
                file_path=str(raw_file_path)
            )

            # Métadonnées publiées dans le bucket raw-logs (traçabilité)
            metadata_object_name = self._build_minio_object_name(
                partition_path=partition_path,
                file_name=metadata_file_path.name
            )
            upload_json(LOGS_BUCKET, metadata_object_name, metadata)

            size_bytes = raw_file_path.stat().st_size

            log_ingestion_success(
                log=log,
                source=self.source_name,
                object_name=object_name,
                file_hash=content_hash,
                size_bytes=size_bytes
            )

            return metadata

        except Exception as exc:
            log_ingestion_error(
                log=log,
                source=self.source_name,
                error=exc,
                context="ingest_publications"
            )

            return self._build_metadata(
                source_url=self.connector.api_connector.build_url(),
                ingestion_timestamp=ingestion_timestamp,
                content_hash="",
                record_count=0,
                status="failed"
            )

    def _build_partition_path(self, ingestion_timestamp: datetime) -> Path:
        year = ingestion_timestamp.strftime("%Y")
        month = ingestion_timestamp.strftime("%m")
        day = ingestion_timestamp.strftime("%d")

        return Path(
            f"source={self.source_name}/year={year}/month={month}/day={day}"
        )

    def _save_raw_payload(
        self,
        records: List[Dict[str, Any]],
        partition_path: Path,
        ingestion_timestamp: datetime,
        content_hash: str
    ) -> Tuple[Path, Path]:
        local_partition_dir = self.local_raw_dir / partition_path
        local_partition_dir.mkdir(parents=True, exist_ok=True)

        timestamp_label = ingestion_timestamp.strftime("%Y%m%dT%H%M%SZ")

        raw_file_path = local_partition_dir / (
            f"openalex_publications_{timestamp_label}_{content_hash[:12]}.json"
        )

        metadata_file_path = local_partition_dir / (
            f"openalex_publications_{timestamp_label}_{content_hash[:12]}_metadata.json"
        )

        with open(raw_file_path, "w", encoding="utf-8") as raw_file:
            json.dump(records, raw_file, ensure_ascii=False, indent=2)

        log.info(f"Saved raw payload locally: {raw_file_path}")

        return raw_file_path, metadata_file_path

    def _build_metadata(
        self,
        source_url: str,
        ingestion_timestamp: datetime,
        content_hash: str,
        record_count: int,
        status: str
    ) -> Dict[str, Any]:
        return {
            "source_system": self.source_name,
            "source_url": source_url,
            "ingestion_timestamp": ingestion_timestamp.isoformat(),
            "content_hash": content_hash,
            "record_count": record_count,
            "status": status
        }

    def _save_metadata(
        self,
        metadata_file_path: Path,
        metadata: Dict[str, Any]
    ) -> None:
        with open(metadata_file_path, "w", encoding="utf-8") as metadata_file:
            json.dump(metadata, metadata_file, ensure_ascii=False, indent=2)

        log.info(f"Saved metadata locally: {metadata_file_path}")

    def _build_minio_object_name(
        self,
        partition_path: Path,
        file_name: str
    ) -> str:
        return str(partition_path / file_name).replace("\\", "/")


def run_api_ingestion() -> Dict[str, Any]:
    """Point d'entrée utilisé par le DAG Airflow."""
    ingestor = APIIngestor(bucket_name="raw-json")
    return ingestor.ingest_publications()


if __name__ == "__main__":
    result_metadata = run_api_ingestion()

    print(json.dumps(result_metadata, indent=2))