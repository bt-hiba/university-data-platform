"""
Détection heuristique des Single Page Applications.

Stratégie : on n'utilise jamais le navigateur tant qu'on a la preuve que la page
servie en statique contient déjà du contenu exploitable. Ce module fournit
`is_spa(html)` qui combine plusieurs signaux faibles.
"""
from __future__ import annotations

import re
from typing import Tuple

from bs4 import BeautifulSoup


# Conteneurs racine typiques des frameworks SPA
_SPA_ROOT_SELECTORS = [
    {"id": "root"},
    {"id": "app"},
    {"id": "__next"},
    {"id": "__nuxt"},
    {"class_": "ember-application"},
]

# Seuil sous lequel on considère que le body est trop pauvre pour être statique
_MIN_TEXT_LENGTH = 200

# Seuil sous lequel on considère qu'il y a "peu" de liens cliquables
_MIN_ANCHOR_COUNT = 3


def is_spa(html: str) -> Tuple[bool, str]:
    """
    Détermine si une page HTML est probablement une SPA.

    Retourne :
        (True, raison)  si la page semble être une SPA
        (False, raison) sinon

    Heuristiques cumulatives :
      1. Conteneur racine connu (`<div id="root">`, `id="app"`, …) vide ou quasi-vide
      2. Texte visible global < `_MIN_TEXT_LENGTH` caractères
      3. Nombre d'ancres `<a href>` < `_MIN_ANCHOR_COUNT`
    """
    if not html or len(html) < 500:
        return True, "html_too_short"

    soup = BeautifulSoup(html, "html.parser")

    for selector in _SPA_ROOT_SELECTORS:
        node = soup.find("div", **selector)
        if node is not None and len(node.get_text(strip=True)) < 50:
            label = selector.get("id") or selector.get("class_")
            return True, f"empty_spa_root[{label}]"

    body = soup.body
    if body is None:
        return True, "no_body_tag"

    text_length = len(body.get_text(strip=True))
    anchor_count = len(body.find_all("a", href=True))

    if text_length < _MIN_TEXT_LENGTH and anchor_count < _MIN_ANCHOR_COUNT:
        return True, f"sparse_body[text={text_length},anchors={anchor_count}]"

    return False, f"static_ok[text={text_length},anchors={anchor_count}]"


def detect_domain(url: str) -> str:
    """Extrait le netloc d'une URL, utile pour matcher les API overrides."""
    match = re.match(r"https?://([^/]+)", url)
    return match.group(1).lower() if match else ""
