"""
Fetcher Playwright — utilisé uniquement en dernier recours (tier 3).

Playwright est volontairement chargé en lazy-import : si le paquet (ou les
binaires Chromium) ne sont pas installés, le crawler dégrade proprement en
journalisant l'incident plutôt que de planter.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class RenderedPage:
    html: str
    final_url: str
    http_status: int


class PlaywrightUnavailable(RuntimeError):
    """Levée si playwright ou ses binaires ne sont pas installés."""


def is_available() -> bool:
    """Indique si Playwright + Chromium sont utilisables sur cette machine."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    try:
        with sync_playwright() as p:
            p.chromium.executable_path
        return True
    except Exception:
        return False


def render(
    url: str,
    timeout_seconds: int = 30,
    wait_until: str = "networkidle",
    user_agent: Optional[str] = None,
) -> RenderedPage:
    """
    Charge une URL avec Chromium headless et retourne le HTML rendu.

    Lève `PlaywrightUnavailable` si l'environnement n'est pas prêt.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise PlaywrightUnavailable(
            "playwright n'est pas installé. Ajouter 'playwright' aux dépendances "
            "et exécuter 'playwright install chromium'."
        ) from exc

    timeout_ms = timeout_seconds * 1000

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=user_agent) if user_agent else browser.new_context()
            page = context.new_page()
            response = page.goto(url, timeout=timeout_ms, wait_until=wait_until)
            html = page.content()
            final_url = page.url
            status = response.status if response is not None else 0
            browser.close()
            return RenderedPage(html=html, final_url=final_url, http_status=status)
    except Exception as exc:
        # Chromium absent ou libs système manquantes
        if "Executable doesn't exist" in str(exc) or "Host system is missing" in str(exc):
            raise PlaywrightUnavailable(str(exc)) from exc
        raise
