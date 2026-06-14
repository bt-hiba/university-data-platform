"""
Registre des APIs déclarées pour les SPAs (tier 2 du crawler).

Charge la section `spa_api_overrides` de `configs/sources.yaml` et expose
`lookup(domain)` qui renvoie la liste des endpoints à interroger lorsque
le domaine sert une Single Page Application.

Convention : l'opérateur inspecte manuellement les appels réseau de la SPA
(DevTools > Network), identifie les endpoints JSON exploitables, puis les
déclare ici. Aucune découverte automatique n'est tentée : c'est explicite
et auditable.
"""
from __future__ import annotations

import os
from typing import Dict, List

import yaml


_CONFIG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "configs", "sources.yaml")
)


def _load_overrides() -> Dict[str, List[Dict]]:
    if not os.path.exists(_CONFIG_PATH):
        return {}
    with open(_CONFIG_PATH, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    overrides = data.get("spa_api_overrides") or {}
    # Normalise les clés en lowercase pour matcher les netloc
    return {k.lower(): v for k, v in overrides.items() if v}


def lookup(domain: str) -> List[Dict]:
    """
    Retourne la liste des APIs configurées pour un domaine (ex. 'fsac.ac.ma').

    Chaque entrée est un dict `{name, url}`. Liste vide si rien n'est déclaré.
    """
    if not domain:
        return []
    overrides = _load_overrides()
    return overrides.get(domain.lower(), [])
