from typing import List, Dict
from urllib.parse import urljoin, urlparse, urldefrag

from bs4 import BeautifulSoup


# Extensions considérées comme documents binaires (vont dans raw-documents)
DOCUMENT_EXTENSIONS = {
    "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "odt", "rtf"
}

# Extensions considérées comme HTML (vont dans raw-html)
HTML_EXTENSIONS = {"html", "htm", "php", "asp", "aspx", "jsp"}


def _classify_link(url: str) -> str:
    """
    Détermine le type de cible d'une URL à partir de son extension.

    Retourne :
        "document"  → PDF / DOC / XLS / PPT
        "html"      → page web (ou pas d'extension détectable)
        "other"     → image, archive, etc. (ignoré par le crawler)
    """
    path = urlparse(url).path.lower()
    if "." not in path.split("/")[-1]:
        # pas d'extension détectable → on suppose que c'est une page HTML
        return "html"

    ext = path.rsplit(".", 1)[-1]
    if ext in DOCUMENT_EXTENSIONS:
        return "document"
    if ext in HTML_EXTENSIONS:
        return "html"
    return "other"


def _normalize_link(href: str, base_url: str) -> str:
    """Résout les URLs relatives et supprime les fragments (#section)."""
    absolute = urljoin(base_url, href)
    defragged, _ = urldefrag(absolute)
    return defragged


def _is_same_domain(url: str, base_url: str) -> bool:
    return urlparse(url).netloc == urlparse(base_url).netloc


def extract_links(html: str, base_url: str, same_domain_only: bool = True) -> List[Dict]:
    """
    Extrait tous les liens cliquables d'une page HTML.

    Arguments :
        html              : contenu HTML brut
        base_url          : URL de la page d'origine (sert à résoudre les liens relatifs)
        same_domain_only  : si True, ne garde que les liens vers le même domaine
                            (évite que le crawler s'évade vers Facebook, Google, etc.)

    Retourne :
        Liste de dicts {"url": str, "type": "html"|"document"}.
        Les doublons et liens "other" sont filtrés.
    """
    soup = BeautifulSoup(html, "html.parser")

    seen = set()
    results: List[Dict] = []

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()

        # Ignorer liens vides, ancres pures, mailto, tel, javascript
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue

        url = _normalize_link(href, base_url)

        if same_domain_only and not _is_same_domain(url, base_url):
            continue

        link_type = _classify_link(url)
        if link_type == "other":
            continue

        if url in seen:
            continue
        seen.add(url)

        results.append({"url": url, "type": link_type})

    return results
