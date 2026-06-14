from typing import Optional

from utils.time_utils import get_timestamp_str


def build_node_metadata(
    node_id: str,
    parent_id: Optional[str],
    depth: int,
    source_url: str,
    content_hash: str,
    bucket: str,
    object_path: str,
    content_type: str = "html",
    http_status: Optional[int] = None,
    source_name: Optional[str] = None,
    render_mode: str = "static",
) -> dict:
    """
    Construit le bloc de métadonnées d'un objet crawlé.

    Schéma exigé par la consigne :
        {
          "node_id":   "1.1.2",
          "parent_id": "1.1",
          "depth":     3,
          "source_url":"https://...",
          "crawl_timestamp":"...",
          "content_hash":"...",
          "bucket":"raw-html",
          "object_path":"..."
        }
    """
    return {
        "node_id":         node_id,
        "parent_id":       parent_id,
        "depth":           depth,
        "source_url":      source_url,
        "crawl_timestamp": get_timestamp_str(),
        "content_hash":    content_hash,
        "bucket":          bucket,
        "object_path":     object_path,
        "content_type":    content_type,
        "http_status":     http_status,
        "source_name":     source_name,
        "render_mode":     render_mode,
    }


def build_node_id(parent_id: Optional[str], child_index: int) -> str:
    """
    Construit le node_id d'un enfant à partir de l'id du parent et de son rang.

    Exemples :
        build_node_id(None, 1)   -> "1"           (racine)
        build_node_id("1", 1)    -> "1.1"
        build_node_id("1.1", 2)  -> "1.1.2"
    """
    if parent_id is None:
        return str(child_index)
    return f"{parent_id}.{child_index}"


def node_id_to_filename(node_id: str, extension: str) -> str:
    """
    Convertit un node_id (avec '.') en nom de fichier MinIO (avec '-').

    Exemples :
        node_id_to_filename("1",     "html") -> "1.html"
        node_id_to_filename("1.1.2", "pdf")  -> "1-1-2.pdf"

    On garde les tirets parce qu'ils sont neutres et stables : aucun nom
    métier ("dept-mi", "droit") n'apparaît, le pipeline reste générique
    quel que soit le site crawlé.
    """
    safe = node_id.replace(".", "-")
    extension = extension.lstrip(".")
    return f"{safe}.{extension}"
