from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
SAMPLE_DATA_DIR = BASE_DIR / "ingestion" / "files" / "sample_data"

import pprint

from ingestion.files.csv_reader import read_csv_file
from ingestion.files.json_reader import read_json_file
from ingestion.files.pdf_reader import read_pdf_file
from ingestion.files.metadata_generator import generate_metadata

from utils.logger import (
    setup_logger,
    log_ingestion_start,
    log_ingestion_success,
    log_ingestion_error
)

from utils.hash_utils import compute_hash_from_file

from storage.minio_client import upload_file
from utils.time_utils import build_minio_date_path


log = setup_logger("file_loader")


def process_csv(file_path):

    try:
        log_ingestion_start(log, file_path, "csv")

        data = read_csv_file(file_path)

        metadata = generate_metadata(file_path, "csv")

        log_ingestion_success(
            log,
            file_path,
            file_path,
            metadata["content_hash"],
            metadata["file_size_bytes"]
        )

        path = build_minio_date_path("csv")

        upload_file(
            "raw-documents",
            f"{path}/courses.csv",
            str(file_path)
        )

        return data, metadata

    except Exception as e:
        log_ingestion_error(log, file_path, e)
        return None, None


def process_json(file_path):

    try:

        log_ingestion_start(
            log,
            file_path,
            "json"
        )

        data = read_json_file(file_path)

        metadata = generate_metadata(
            file_path,
            "json"
        )

        log_ingestion_success(
            log,
            file_path,
            file_path,
            metadata["content_hash"],
            metadata["file_size_bytes"]
        )
        path = build_minio_date_path("json")

        upload_file(
            "raw-json",
            f"{path}/faculties.json",
            str(file_path)
        )

        return data, metadata

    except Exception as e:

        log_ingestion_error(
            log,
            file_path,
            e
        )


def process_pdf(file_path):

    try:

        log_ingestion_start(
            log,
            file_path,
            "pdf"
        )

        text = read_pdf_file(file_path)

        metadata = generate_metadata(
            file_path,
            "pdf"
        )

        log_ingestion_success(
            log,
            file_path,
            file_path,
            metadata["content_hash"],
            metadata["file_size_bytes"]
        )
        path = build_minio_date_path("pdf")

        upload_file(
            "raw-documents",
            f"{path}/guide.pdf",
            str(file_path)
        )

        return text, metadata

    except Exception as e:

        log_ingestion_error(
            log,
            file_path,
            e
        )

def run_files():

    csv_data, csv_meta = process_csv(
        SAMPLE_DATA_DIR / "courses.csv"
    )

    json_data, json_meta = process_json(
        SAMPLE_DATA_DIR / "faculties.json"
    )

    pdf_text, pdf_meta = process_pdf(
        SAMPLE_DATA_DIR / "guide.pdf"
    )

    return {
        "csv": csv_meta,
        "json": json_meta,
        "pdf": pdf_meta
    }

if __name__ == "__main__":

    results = run_files()

    print("\nCSV Metadata")
    pprint.pprint(results["csv"])

    print("\nJSON Metadata")
    pprint.pprint(results["json"])

    print("\nPDF Metadata")
    pprint.pprint(results["pdf"])