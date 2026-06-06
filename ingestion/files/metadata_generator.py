import os

from utils.hash_utils import compute_hash_from_file
from utils.time_utils import get_timestamp_str


def generate_metadata(
        file_path,
        source_type
):

    return {

        "source_type": source_type,

        "file_name": os.path.basename(file_path),

        "file_size_bytes": os.path.getsize(file_path),

        "content_hash": compute_hash_from_file(file_path),

        "ingestion_timestamp": get_timestamp_str()

    }