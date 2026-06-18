
import os
import sys
from loguru import logger
from utils.time_utils import get_date_parts


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION DU LOGGER
# ─────────────────────────────────────────────────────────────────────────────

def setup_logger(component: str = "pipeline") -> None:
    """
    Configure le système de logs pour le projet.

    Cette fonction doit être appelée UNE SEULE FOIS au démarrage
    de chaque script (par les Membres 2, 3, 4, 6 dans leurs fichiers).

    Elle configure deux "destinations" pour les logs :
    1. La console (terminal) → pour voir les logs en temps réel
    2. Un fichier sur le disque → pour garder une trace durable

    Argument :
        component (str) : nom du composant qui génère les logs
                          (ex: "api_ingestor", "web_scraper", "file_loader")
                          Cela permet d'identifier quelle partie du code
                          a généré chaque log.
    """

    # On supprime tous les handlers existants pour repartir proprement.
    # Un "handler" est une destination vers laquelle les logs sont envoyés.
    # Sans cette ligne, si setup_logger() est appelé plusieurs fois,
    # les logs seraient dupliqués.
    logger.remove()

    # ── Handler 1 : Console (terminal) ───────────────────────────────────────
    # On ajoute un handler qui affiche les logs dans le terminal.
    # Le format est : heure | niveau | composant | message
    logger.add(
        sys.stdout,

        # Format du message affiché dans le terminal
        # {time} : heure du log
        # {level} : niveau (INFO, WARNING, ERROR...)
        # {extra[component]} : le nom du composant passé en argument
        # {message} : le texte du log
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{extra[component]: <15}</cyan> | "
            "{message}"
        ),

        # Niveau minimum : on affiche tous les logs de niveau INFO et au-dessus
        # (INFO, SUCCESS, WARNING, ERROR, CRITICAL)
        # Les logs DEBUG ne s'affichent pas en production
        level="INFO",

        # Coloriser la sortie pour une meilleure lisibilité dans le terminal
        colorize=True,
    )

    # ── Handler 2 : Fichier de log ────────────────────────────────────────────
    # Base configurable via la variable d'env INGESTION_LOG_DIR.
    # - En local         : ./logs/YYYY/MM/DD/<component>.log
    # - Dans Airflow     : /opt/airflow/logs/ingestion/YYYY/MM/DD/<component>.log
    # On écrit en parallèle des logs Airflow natifs (qui restent gérés par
    # Airflow lui-même via stdout) pour conserver une trace dédiée au pipeline.
    date_parts = get_date_parts()
    base_log_dir = os.getenv("INGESTION_LOG_DIR", "logs")
    log_dir = os.path.join(
        base_log_dir,
        date_parts["year"],
        date_parts["month"],
        date_parts["day"],
    )

    try:
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"{component}.log")
        logger.add(
            log_file,
            level="DEBUG",
            format=(
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                "{level: <8} | "
                "{extra[component]: <15} | "
                "{name}:{function}:{line} | "
                "{message}"
            ),
            rotation="10 MB",
            retention="7 days",
            encoding="utf-8",
        )
    except (OSError, PermissionError):
        # Si l'écriture sur disque est impossible (FS read-only, perms),
        # on ne casse pas le pipeline : on continue en console seulement.
        pass

    # On "lie" le composant au logger pour qu'il apparaisse dans chaque message.
    # bind() crée une copie du logger avec des informations contextuelles fixes.
    return logger.bind(component=component)


# ─────────────────────────────────────────────────────────────────────────────
# FONCTIONS DE LOG MÉTIER
# Ces fonctions sont des raccourcis pratiques que les autres membres
# pourront appeler directement sans se soucier du format.
# ─────────────────────────────────────────────────────────────────────────────

def log_ingestion_start(log, source: str, source_type: str) -> None:
    """
    Log le début d'une ingestion.

    Arguments :
        log         : le logger configuré (retourné par setup_logger)
        source      : identifiant de la source (ex: "openalex", "um5")
        source_type : type de source ("api", "web", "file")
    """
    log.info(f"[START] Ingestion démarrée | source={source} | type={source_type}")


def log_ingestion_success(log, source: str, object_name: str, file_hash: str, size_bytes: int) -> None:
    """
    Log une ingestion réussie avec ses métadonnées.

    Arguments :
        log         : le logger configuré
        source      : identifiant de la source
        object_name : chemin de l'objet dans MinIO
        file_hash   : checksum SHA-256 du fichier
        size_bytes  : taille du fichier en bytes
    """
    log.success(
        f"[OK] Upload réussi | "
        f"source={source} | "
        f"objet={object_name} | "
        f"hash={file_hash[:12]}... | "   # on affiche seulement les 12 premiers caractères
        f"taille={size_bytes} bytes"      # pour garder les logs lisibles
    )


def log_ingestion_error(log, source: str, error: Exception, context: str = "") -> None:
    """
    Log une erreur pendant l'ingestion.

    Arguments :
        log     : le logger configuré
        source  : identifiant de la source
        error   : l'exception Python capturée
        context : information supplémentaire sur le contexte de l'erreur
    """
    log.error(
        f"[ERREUR] Échec ingestion | "
        f"source={source} | "
        f"contexte={context} | "
        f"erreur={type(error).__name__}: {str(error)}"
    )


def log_metadata(log, metadata: dict) -> None:
    """
    Log les métadonnées complètes d'un objet ingéré.
    Utile pour la traçabilité et le débogage.

    Argument :
        metadata (dict) : dictionnaire de métadonnées (source, hash, timestamp...)
    """
    log.debug(f"[METADATA] {metadata}")


def log_retry(log, source: str, attempt: int, max_attempts: int, wait_seconds: int) -> None:
    """
    Log une tentative de retry (nouvelle tentative après un échec).

    Cette fonction permet de logger chaque tentative.

    Arguments :
        log          : le logger configuré
        source       : identifiant de la source
        attempt      : numéro de la tentative actuelle (commence à 1)
        max_attempts : nombre maximum de tentatives
        wait_seconds : temps d'attente avant cette tentative (en secondes)
    """
    log.warning(
        f"[RETRY] Nouvelle tentative | "
        f"source={source} | "
        f"tentative={attempt}/{max_attempts} | "
        f"attente={wait_seconds}s"
    )