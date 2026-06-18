import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from ingestion.api.api_ingestor import APIIngestor
from utils.hash_utils import (
    compute_hash_from_bytes,
    compute_hash_from_file,
    compute_hash_from_text,
)


def test_compute_hash_from_text_is_stable_for_same_text():
    text = "OpenAlex publication data"

    hash_one = compute_hash_from_text(text)
    hash_two = compute_hash_from_text(text)

    assert hash_one == hash_two
    assert len(hash_one) == 64


def test_compute_hash_from_bytes_is_stable_for_same_bytes():
    data = b"OpenAlex publication data"

    hash_one = compute_hash_from_bytes(data)
    hash_two = compute_hash_from_bytes(data)

    assert hash_one == hash_two
    assert len(hash_one) == 64


def test_compute_hash_from_file_reads_file_content(tmp_path):
    file_path = tmp_path / "sample.json"
    file_path.write_text('{"source": "openalex"}', encoding="utf-8")

    file_hash = compute_hash_from_file(str(file_path))

    assert len(file_hash) == 64


def test_build_partition_path_uses_source_and_date():
    mock_connector = MagicMock()

    ingestor = APIIngestor(
        bucket_name="test-bucket",
        local_raw_dir="test-data",
        source_name="openalex",
        connector=mock_connector
    )

    ingestion_timestamp = datetime(2026, 6, 6, 10, 30, tzinfo=timezone.utc)

    partition_path = ingestor._build_partition_path(ingestion_timestamp)

    assert partition_path == Path(
        "source=openalex/year=2026/month=06/day=06"
    )


def test_build_metadata_contains_required_fields():
    mock_connector = MagicMock()

    ingestor = APIIngestor(
        bucket_name="test-bucket",
        local_raw_dir="test-data",
        source_name="openalex",
        connector=mock_connector
    )

    ingestion_timestamp = datetime(2026, 6, 6, 10, 30, tzinfo=timezone.utc)

    metadata = ingestor._build_metadata(
        source_url="https://api.openalex.org/works",
        ingestion_timestamp=ingestion_timestamp,
        content_hash="abc123",
        record_count=2,
        status="success"
    )

    assert metadata == {
        "source_system": "openalex",
        "source_url": "https://api.openalex.org/works",
        "ingestion_timestamp": "2026-06-06T10:30:00+00:00",
        "content_hash": "abc123",
        "record_count": 2,
        "status": "success"
    }


def test_build_minio_object_name_uses_forward_slashes():
    mock_connector = MagicMock()

    ingestor = APIIngestor(
        bucket_name="test-bucket",
        local_raw_dir="test-data",
        source_name="openalex",
        connector=mock_connector
    )

    partition_path = Path("source=openalex/year=2026/month=06/day=06")

    object_name = ingestor._build_minio_object_name(
        partition_path=partition_path,
        file_name="openalex_publications.json"
    )

    assert object_name == (
        "source=openalex/year=2026/month=06/day=06/"
        "openalex_publications.json"
    )


def test_save_raw_payload_and_metadata_creates_json_files(tmp_path):
    mock_connector = MagicMock()

    ingestor = APIIngestor(
        bucket_name="test-bucket",
        local_raw_dir=str(tmp_path),
        source_name="openalex",
        connector=mock_connector
    )

    records = [
        {
            "id": "https://openalex.org/W123",
            "title": "Example Publication"
        }
    ]

    ingestion_timestamp = datetime(2026, 6, 6, 10, 30, tzinfo=timezone.utc)

    raw_json_text = json.dumps(
        records,
        ensure_ascii=False,
        sort_keys=True
    )

    content_hash = compute_hash_from_text(raw_json_text)
    partition_path = ingestor._build_partition_path(ingestion_timestamp)

    raw_file_path, metadata_file_path = ingestor._save_raw_payload(
        records=records,
        partition_path=partition_path,
        ingestion_timestamp=ingestion_timestamp,
        content_hash=content_hash
    )

    metadata = ingestor._build_metadata(
        source_url="https://api.openalex.org/works",
        ingestion_timestamp=ingestion_timestamp,
        content_hash=content_hash,
        record_count=len(records),
        status="success"
    )

    ingestor._save_metadata(metadata_file_path, metadata)

    assert raw_file_path.exists()
    assert metadata_file_path.exists()

    with open(raw_file_path, "r", encoding="utf-8") as raw_file:
        saved_records = json.load(raw_file)

    with open(metadata_file_path, "r", encoding="utf-8") as metadata_file:
        saved_metadata = json.load(metadata_file)

    assert saved_records == records
    assert saved_metadata["source_system"] == "openalex"
    assert saved_metadata["record_count"] == 1
    assert saved_metadata["status"] == "success"


@patch("ingestion.api.api_ingestor.upload_json")
@patch("ingestion.api.api_ingestor.upload_file")
def test_ingest_publications_fetches_saves_metadata_and_uploads(
    mock_upload_file,
    mock_upload_json,
    tmp_path
):
    mock_connector = MagicMock()
    mock_connector.fetch_publications.return_value = [
        {
            "id": "https://openalex.org/W123",
            "title": "Example Publication"
        },
        {
            "id": "https://openalex.org/W456",
            "title": "Another Publication"
        }
    ]
    mock_connector.api_connector.build_url.return_value = (
        "https://api.openalex.org/works"
    )

    ingestor = APIIngestor(
        bucket_name="test-bucket",
        local_raw_dir=str(tmp_path),
        source_name="openalex",
        connector=mock_connector
    )

    metadata = ingestor.ingest_publications()

    assert metadata["source_system"] == "openalex"
    assert metadata["source_url"] == "https://api.openalex.org/works"
    assert metadata["record_count"] == 2
    assert metadata["status"] == "success"
    assert len(metadata["content_hash"]) == 64

    mock_connector.fetch_publications.assert_called_once()
    mock_upload_file.assert_called_once()
    mock_upload_json.assert_called_once()

    upload_call_kwargs = mock_upload_file.call_args.kwargs

    assert upload_call_kwargs["bucket_name"] == "test-bucket"
    assert upload_call_kwargs["object_name"].startswith(
        "source=openalex/year="
    )
    assert upload_call_kwargs["object_name"].endswith(".json")

    metadata_call_args = mock_upload_json.call_args.args
    assert metadata_call_args[0] == "raw-logs"



# ─── SPA detection (tier 3 fallback) ─────────────────────────────────────────

from ingestion.web.spa_detector import detect_domain, is_spa


_STATIC_HTML = """
<html><body>
  <h1>Faculté des Sciences</h1>
  <p>Bienvenue sur le site officiel. Cette page présente nos formations,
     notre actualité et nos coordonnées de contact.</p>
  <ul>
    <li><a href="/formations">Formations</a></li>
    <li><a href="/recherche">Recherche</a></li>
    <li><a href="/contact">Contact</a></li>
    <li><a href="/annonces">Annonces</a></li>
  </ul>
</body></html>
""" * 3


_SPA_HEAD = """
<!doctype html><html lang="fr"><head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <meta name="description" content="University SPA" />
  <link rel="icon" href="/favicon.ico" />
  <link rel="manifest" href="/manifest.json" />
  <link rel="stylesheet" href="/static/css/main.abc123.css" />
  <title>University Portal</title>
</head>
""".strip()


_SPA_HTML_ROOT = _SPA_HEAD + """
<body>
  <noscript>You need to enable JavaScript to run this app.</noscript>
  <div id="root"></div>
  <script src="/static/js/runtime.abc.js"></script>
  <script src="/static/js/vendor.def.js"></script>
  <script src="/static/js/main.abc123.js"></script>
</body></html>
"""


_SPA_HTML_APP = _SPA_HEAD + """
<body>
  <noscript>This site requires JavaScript.</noscript>
  <div id="app"></div>
  <script src="/static/js/vendor.js"></script>
  <script src="/static/js/app.js"></script>
</body></html>
"""


def test_is_spa_returns_false_for_static_html():
    spa, reason = is_spa(_STATIC_HTML)
    assert spa is False
    assert reason.startswith("static_ok")


def test_is_spa_detects_react_root():
    spa, reason = is_spa(_SPA_HTML_ROOT)
    assert spa is True
    assert "root" in reason


def test_is_spa_detects_vue_app():
    spa, reason = is_spa(_SPA_HTML_APP)
    assert spa is True
    assert "app" in reason


def test_is_spa_handles_empty_html():
    spa, reason = is_spa("")
    assert spa is True
    assert reason == "html_too_short"


def test_detect_domain_extracts_netloc():
    assert detect_domain("https://fsac.ac.ma/page.html") == "fsac.ac.ma"
    assert detect_domain("http://example.org") == "example.org"
    assert detect_domain("not-a-url") == ""


def test_build_node_metadata_includes_render_mode():
    from ingestion.web.metadata_builder import build_node_metadata

    meta = build_node_metadata(
        node_id="1",
        parent_id=None,
        depth=1,
        source_url="https://x.test",
        content_hash="a" * 64,
        bucket="raw-html",
        object_path="source=x/year=2026/month=01/day=01/1.html",
        render_mode="playwright",
    )
    assert meta["render_mode"] == "playwright"
    assert meta["node_id"] == "1"
