import os
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import requests

from ingestion.web import playwright_fetcher, spa_api_registry
from ingestion.web.link_extractor import extract_links
from ingestion.web.metadata_builder import (
    build_node_id,
    build_node_metadata,
    node_id_to_filename,
)
from ingestion.web.spa_detector import detect_domain, is_spa
from storage.minio_client import upload_bytes, upload_html, upload_json
from utils.hash_utils import compute_hash_from_bytes, compute_hash_from_text
from utils.logger import setup_logger
from utils.time_utils import build_minio_date_path


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; UniversityDataPlatform/1.0; +https://example.org/bot)"
    )
}

HTML_BUCKET = "raw-html"
JSON_BUCKET = "raw-json"
DOCUMENT_BUCKET = "raw-documents"
LOGS_BUCKET = "raw-logs"


@dataclass
class CrawlConfig:
    root_url: str
    source_name: str
    max_depth: int = 2
    max_pages: int = 30
    request_timeout: int = 30
    max_retries: int = 3
    same_domain_only: bool = True
    enable_playwright: bool = True


@dataclass
class _Task:
    url: str
    node_id: str
    parent_id: Optional[str]
    depth: int
    kind: str  # "html" | "document"


@dataclass
class CrawlResult:
    pages_crawled: int = 0
    documents_downloaded: int = 0
    failures: int = 0
    metadata_records: List[Dict] = field(default_factory=list)


def _http_get(url: str, timeout: int, max_retries: int, log) -> Optional[requests.Response]:
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as exc:
            log.warning(
                f"[HTTP RETRY] attempt={attempt}/{max_retries} | url={url} | error={exc}"
            )
    log.error(f"[HTTP ABANDON] url={url} | toutes les tentatives ont échoué")
    return None


def _save_metadata(metadata: Dict, source_name: str) -> None:
    """Pousse le bloc de métadonnées d'un objet dans le bucket raw-logs."""
    date_path = build_minio_date_path(source_name)
    object_path = (
        f"{date_path}/metadata_{metadata['node_id'].replace('.', '-')}.json"
    )
    upload_json(LOGS_BUCKET, object_path, metadata)


def _fetch_html_with_strategy(
    url: str,
    config: CrawlConfig,
    log,
) -> Optional[Tuple[str, int, str]]:
    """
    Cascade de récupération HTML en 3 tiers, dans l'ordre de coût croissant :

        Tier 1 — requests + bs4              (render_mode='static')
        Tier 2 — API déclarée pour ce domaine (render_mode='api')
        Tier 3 — Playwright (Chromium)       (render_mode='playwright')

    Le tier 2 prend la main si une SPA est détectée ET qu'une override est
    déclarée dans `configs/sources.yaml` ; sinon on tombe sur Playwright.
    Si Playwright n'est pas disponible, on retourne le HTML "pauvre" du
    tier 1 plutôt que rien — le sidecar trace explicitement l'incident.

    Retour : (html, http_status, render_mode) ou None si échec total.
    """
    # ── Tier 1 ────────────────────────────────────────────────────────────
    response = _http_get(url, config.request_timeout, config.max_retries, log)
    if response is None:
        return None

    html = response.text
    spa, reason = is_spa(html)
    if not spa:
        log.info(f"[TIER 1 STATIC] url={url} | {reason}")
        return html, response.status_code, "static"

    log.warning(f"[SPA DETECTED] url={url} | reason={reason}")

    # ── Tier 2 ────────────────────────────────────────────────────────────
    domain = detect_domain(url)
    overrides = spa_api_registry.lookup(domain)
    if overrides:
        log.info(f"[TIER 2 API] domain={domain} | endpoints={len(overrides)}")
        # On retourne le HTML brut (tier 1) pour conserver la traçabilité du
        # node racine, mais on déclenche en parallèle l'ingestion des APIs.
        _ingest_spa_apis(overrides, config, log)
        return html, response.status_code, "api"

    # ── Tier 3 ────────────────────────────────────────────────────────────
    if not config.enable_playwright:
        log.warning(f"[TIER 3 SKIPPED] playwright désactivé | url={url}")
        return html, response.status_code, "static"

    if not playwright_fetcher.is_available():
        log.warning(
            f"[TIER 3 UNAVAILABLE] playwright/chromium absent | url={url} | "
            "fallback sur HTML statique pauvre"
        )
        return html, response.status_code, "static"

    try:
        rendered = playwright_fetcher.render(
            url=url,
            timeout_seconds=config.request_timeout,
            user_agent=HEADERS["User-Agent"],
        )
        log.success(f"[TIER 3 PLAYWRIGHT] url={url} | status={rendered.http_status}")
        return rendered.html, rendered.http_status, "playwright"
    except playwright_fetcher.PlaywrightUnavailable as exc:
        log.warning(f"[TIER 3 FALLBACK] url={url} | {exc}")
        return html, response.status_code, "static"


def _ingest_spa_apis(overrides: List[Dict], config: CrawlConfig, log) -> None:
    """
    Tier 2 — appelle chaque API déclarée pour ce domaine et stocke la réponse
    JSON brute dans raw-json. Volontairement séparé du flux node_id principal :
    les données API sont indexées par leur `name` métier, pas par hiérarchie.
    """
    from utils.time_utils import build_minio_date_path

    date_path = build_minio_date_path(config.source_name)
    for entry in overrides:
        api_url = entry.get("url")
        api_name = entry.get("name") or "api"
        if not api_url:
            continue
        response = _http_get(api_url, config.request_timeout, config.max_retries, log)
        if response is None:
            continue
        try:
            payload = response.json()
        except ValueError:
            log.warning(f"[TIER 2 NON-JSON] url={api_url}")
            continue
        object_path = f"{date_path}/spa_api_{api_name}.json"
        upload_json(JSON_BUCKET, object_path, payload)
        log.success(f"[TIER 2 UPLOAD] api={api_name} | object={object_path}")


def crawl(config: CrawlConfig) -> CrawlResult:
    """
    Crawler générique en largeur (BFS) avec node_id hiérarchique.

    L'arbre construit :
        1                <- racine (root_url)
        ├── 1.1          <- premier lien interne trouvé
        │   ├── 1.1.1
        │   └── 1.1.2.pdf
        └── 1.2
    """
    log = setup_logger("crawler")
    log.info(f"[START CRAWL] source={config.source_name} | root={config.root_url}")

    result = CrawlResult()
    visited: Set[str] = set()
    date_path = build_minio_date_path(config.source_name)

    queue: deque = deque([
        _Task(url=config.root_url, node_id="1", parent_id=None, depth=1, kind="html")
    ])

    while queue and result.pages_crawled + result.documents_downloaded < config.max_pages:
        task = queue.popleft()
        if task.url in visited:
            continue
        visited.add(task.url)

        log.info(f"[URL FOUND] node={task.node_id} | depth={task.depth} | url={task.url}")

        try:
            if task.kind == "document":
                response = _http_get(task.url, config.request_timeout, config.max_retries, log)
                if response is None:
                    result.failures += 1
                    continue
                payload = response.content
                content_hash = compute_hash_from_bytes(payload)
                extension = os.path.splitext(task.url.split("?")[0])[1].lstrip(".") or "bin"
                file_name = node_id_to_filename(task.node_id, extension)
                object_path = f"{date_path}/{file_name}"
                upload_bytes(
                    DOCUMENT_BUCKET,
                    object_path,
                    payload,
                    content_type=response.headers.get("content-type", "application/octet-stream"),
                )
                log.success(f"[PDF DOWNLOADED] node={task.node_id} | object={object_path}")
                bucket = DOCUMENT_BUCKET
                result.documents_downloaded += 1
                content_type = extension
                render_mode = "static"
                http_status = response.status_code
                html_for_links: Optional[str] = None
            else:
                fetched = _fetch_html_with_strategy(task.url, config, log)
                if fetched is None:
                    result.failures += 1
                    continue
                html, http_status, render_mode = fetched
                content_hash = compute_hash_from_text(html)
                file_name = node_id_to_filename(task.node_id, "html")
                object_path = f"{date_path}/{file_name}"
                upload_html(HTML_BUCKET, object_path, html)
                log.success(
                    f"[UPLOAD SUCCESS] node={task.node_id} | mode={render_mode} | "
                    f"object={object_path}"
                )
                bucket = HTML_BUCKET
                result.pages_crawled += 1
                content_type = "html"
                html_for_links = html

            metadata = build_node_metadata(
                node_id=task.node_id,
                parent_id=task.parent_id,
                depth=task.depth,
                source_url=task.url,
                content_hash=content_hash,
                bucket=bucket,
                object_path=object_path,
                content_type=content_type,
                http_status=http_status,
                source_name=config.source_name,
                render_mode=render_mode,
            )
            _save_metadata(metadata, config.source_name)
            result.metadata_records.append(metadata)

            # Si HTML et profondeur restante, on extrait les liens enfants
            if html_for_links is not None and task.depth < config.max_depth:
                children = extract_links(
                    html=html_for_links,
                    base_url=task.url,
                    same_domain_only=config.same_domain_only,
                )
                for index, child in enumerate(children, start=1):
                    if child["url"] in visited:
                        continue
                    queue.append(_Task(
                        url=child["url"],
                        node_id=build_node_id(task.node_id, index),
                        parent_id=task.node_id,
                        depth=task.depth + 1,
                        kind=child["type"],
                    ))

        except Exception as exc:
            log.error(f"[ERROR] node={task.node_id} | url={task.url} | {exc}")
            result.failures += 1

    log.info(
        f"[FINISH CRAWL] pages={result.pages_crawled} | "
        f"docs={result.documents_downloaded} | failures={result.failures}"
    )
    return result


def run_crawler_from_env() -> CrawlResult:
    """Point d'entrée utilisé par le DAG Airflow."""
    config = CrawlConfig(
        root_url=os.getenv("CRAWLER_ROOT_URL", "https://www.um5.ac.ma/"),
        source_name=os.getenv("CRAWLER_SOURCE_NAME", "um5"),
        max_depth=int(os.getenv("CRAWLER_MAX_DEPTH", "3")),
        max_pages=int(os.getenv("CRAWLER_MAX_PAGES", "30")),
        request_timeout=int(os.getenv("CRAWLER_REQUEST_TIMEOUT", "30")),
        enable_playwright=os.getenv("CRAWLER_ENABLE_PLAYWRIGHT", "true").lower() == "true",
    )
    return crawl(config)


if __name__ == "__main__":
    run_crawler_from_env()
