import os
import json
import time
import requests
import yaml

from utils.logger import (
    setup_logger,
    log_ingestion_start,
    log_ingestion_success,
    log_ingestion_error,
    log_metadata,
    log_retry,
)

# On l'utilise AVANT de sauvegarder pour obtenir l'empreinte du contenu brut.
from utils.hash_utils import compute_hash_from_text

#   On s'en sert pour créer le dossier local.
from utils.time_utils import get_timestamp_str, build_minio_date_path, get_date_parts


# vers un bucket MinIO. On ne modifie pas cette fonction.
from storage.minio_client import upload_file

# CONSTANTES
# renomme le bucket, il suffit de changer cette ligne.
BUCKET_NAME = "raw-web-html"

# Dossier local temporaire où on sauvegarde le HTML avant de l'uploader.
LOCAL_BASE_DIR = os.path.join("raw_data", "web")

# Chemin vers le fichier de configuration qui liste les universités.
SOURCES_CONFIG_PATH = os.path.join("configs", "sources.yaml")

# Paramètres pour les tentatives en cas d'échec réseau.
MAX_RETRIES = 3
RETRY_WAIT = 5

# En-têtes HTTP envoyés avec chaque requête.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


# ─────────────────────────────────────────────────────────────────────────────
# FONCTION 1 : Lire la configuration des sources
# ─────────────────────────────────────────────────────────────────────────────

def load_university_sources(config_path: str) -> list:
    # Ouvrir le fichier YAML en lecture, encodage UTF-8 pour les accents
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    # Si la clé n'existe pas, on retourne une liste vide (pas d'erreur).
    return config.get("universities", [])


# ─────────────────────────────────────────────────────────────────────────────
# FONCTION 2 : Télécharger le HTML d'une page
# ─────────────────────────────────────────────────────────────────────────────

def download_html(url: str, log, source_name: str) -> str | None:
    # On essaie jusqu'à MAX_RETRIES fois
    for attempt in range(1, MAX_RETRIES + 1):

        try:
            if attempt > 1:
                log_retry(log, source_name, attempt, MAX_RETRIES, RETRY_WAIT)
                time.sleep(RETRY_WAIT)

            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            return response.text

        except requests.exceptions.Timeout:
            # Le serveur a mis plus de 30 secondes à répondre.
            log_ingestion_error(
                log, source_name,
                Exception("Timeout après 30s"),
                context=f"tentative {attempt}/{MAX_RETRIES}"
            )

        except requests.exceptions.ConnectionError:
            log_ingestion_error(
                log, source_name,
                Exception("Erreur de connexion"),
                context=f"tentative {attempt}/{MAX_RETRIES} | url={url}"
            )

        except requests.exceptions.HTTPError as e:
            log_ingestion_error(log, source_name, e, context=f"HTTP error | url={url}")
            return None

        except Exception as e:
            log_ingestion_error(log, source_name, e, context=f"tentative {attempt}/{MAX_RETRIES}")

    # Si on arrive ici, toutes les tentatives ont échoué.
    log.error(f"[ABANDON] {source_name} | Toutes les tentatives ont échoué | url={url}")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# FONCTION 3 : Sauvegarder le HTML localement
# ─────────────────────────────────────────────────────────────────────────────

def save_html_locally(html_content: str, source_name: str) -> str:
    
    date_parts = get_date_parts()

    local_dir = os.path.join(
        LOCAL_BASE_DIR,
        date_parts["year"],
        date_parts["month"],
        date_parts["day"],
        source_name
    )

    os.makedirs(local_dir, exist_ok=True)

    file_path = os.path.join(local_dir, f"{source_name}.html")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return file_path


# ─────────────────────────────────────────────────────────────────────────────
# FONCTION 4 : Créer les métadonnées
# ─────────────────────────────────────────────────────────────────────────────

def build_metadata(source_name: str, url: str, file_hash: str,
                   file_path: str, object_name: str) -> dict:
    return {
        # Identification de la source
        "source_name":   source_name,
        "source_type":   "web",
        "url":           url,

        # Traçabilité
        "ingested_at":   get_timestamp_str(),   # horodatage ISO 8601
        "pipeline":      "web_scraping",

        # Intégrité du fichier
        "hash_sha256":   file_hash,
        "hash_algorithm": "sha256",

        # Localisation
        "local_path":    file_path,
        "minio_bucket":  BUCKET_NAME,
        "minio_object":  object_name,
    }


# ─────────────────────────────────────────────────────────────────────────────
# FONCTION 5 : Sauvegarder les métadonnées localement
# ─────────────────────────────────────────────────────────────────────────────

def save_metadata_locally(metadata: dict, html_file_path: str) -> str:
    metadata_path = html_file_path.replace(".html", "_metadata.json")

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return metadata_path


# ─────────────────────────────────────────────────────────────────────────────
# FONCTION 6 : Pipeline complet pour une université
# ─────────────────────────────────────────────────────────────────────────────

def scrape_university(university: dict, log) -> bool:
    source_name = university["name"]
    url = university["url"]

    # ── Étape 1 : Log du début ────────────────────────────────────────────────
    log_ingestion_start(log, source=source_name, source_type="web")

    # ── Étape 2 : Téléchargement du HTML ─────────────────────────────────────
    html_content = download_html(url, log, source_name)

    # Si le téléchargement a échoué (toutes les tentatives),
    # on arrête le pipeline pour cette université et on retourne False.
    if html_content is None:
        return False

    # ── Étape 3 : Calcul du hash SHA-256 ─────────────────────────────────────
    file_hash = compute_hash_from_text(html_content, encoding="utf-8")

    # ── Étape 4 : Sauvegarde locale du HTML ──────────────────────────────────
    file_path = save_html_locally(html_content, source_name)
    log.debug(f"[LOCAL] HTML sauvegardé | source={source_name} | chemin={file_path}")

    # ── Étape 5 : Construction du chemin MinIO et des métadonnées ────────────
    date_path = build_minio_date_path(source_name)
    object_name = f"{date_path}/{source_name}.html"

    metadata = build_metadata(source_name, url, file_hash, file_path, object_name)

    # ── Étape 6 : Sauvegarde locale des métadonnées ──────────────────────────
    metadata_path = save_metadata_locally(metadata, file_path)
    log_metadata(log, metadata)
    log.debug(f"[LOCAL] Métadonnées sauvegardées | chemin={metadata_path}")

    # ── Étape 7 : Upload dans MinIO ───────────────────────────────────────────
    try:
        upload_file(
            bucket_name=BUCKET_NAME,
            object_name=object_name,
            file_path=file_path
        )
    except Exception as e:
        log_ingestion_error(log, source_name, e, context="upload MinIO")
        return False

    # ── Étape 8 : Log du succès ───────────────────────────────────────────────
    file_size = os.path.getsize(file_path)   # taille du fichier en bytes
    log_ingestion_success(
        log,
        source=source_name,
        object_name=object_name,
        file_hash=file_hash,
        size_bytes=file_size
    )

    return True


# ─────────────────────────────────────────────────────────────────────────────
# FONCTION PRINCIPALE : Point d'entrée du scraper
# ─────────────────────────────────────────────────────────────────────────────
def run_web_scraping() -> None:
    # ── Étape 1 : Configurer le logger ────────────────────────────────────────
    log = setup_logger("web_scraper")
    log.info("=" * 60)
    log.info("Démarrage du scraper web universitaire")
    log.info("=" * 60)

    # ── Étape 2 : Lire la liste des universités ───────────────────────────────
    try:
        universities = load_university_sources(SOURCES_CONFIG_PATH)
    except FileNotFoundError:
        log.error(f"[CONFIG] Fichier introuvable : {SOURCES_CONFIG_PATH}")
        log.error("Vérifier que configs/sources.yaml existe et est accessible.")
        return
    except yaml.YAMLError as e:
        log.error(f"[CONFIG] Erreur de lecture YAML : {e}")
        return

    if not universities:
        log.warning("[CONFIG] Aucune université trouvée dans sources.yaml")
        return

    log.info(f"[CONFIG] {len(universities)} université(s) à scraper : "
             f"{[u['name'] for u in universities]}")

    # ── Étape 3 : Scraper chaque université ───────────────────────────────────
    success_count = 0
    failure_count = 0

    for university in universities:
        # scrape_university() retourne True si tout s'est bien passé.
        success = scrape_university(university, log)

        if success:
            success_count += 1
        else:
            failure_count += 1

    # ── Étape 4 : Rapport final ───────────────────────────────────────────────
    log.info("=" * 60)
    log.info(f"[FIN] Scraping terminé | "
             f"succès={success_count} | "
             f"échecs={failure_count} | "
             f"total={len(universities)}")
    log.info("=" * 60)

# EXÉCUTION DIRECTE (pour tester le scraper sans passer par main_ingestion.py)
if __name__ == "__main__":
    run_web_scraping()