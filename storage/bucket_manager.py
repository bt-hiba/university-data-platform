from pathlib import Path
from typing import List

import yaml

from storage.minio_client import get_client
from utils.logger import setup_logger


CONFIG_PATH = Path(__file__).resolve().parent.parent / "configs" / "minio_config.yaml"


def load_bucket_names(config_path: Path = CONFIG_PATH) -> List[str]:
    with open(config_path, "r", encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file) or {}
    return list((config.get("buckets") or {}).keys())


def ensure_buckets(bucket_names: List[str] = None) -> List[str]:
    log = setup_logger("bucket_manager")
    client = get_client()

    if bucket_names is None:
        bucket_names = load_bucket_names()

    created = []
    for bucket in bucket_names:
        if client.bucket_exists(bucket):
            log.info(f"[BUCKET OK] {bucket} already exists")
        else:
            client.make_bucket(bucket)
            created.append(bucket)
            log.success(f"[BUCKET CREATED] {bucket}")
    return created


if __name__ == "__main__":
    ensure_buckets()