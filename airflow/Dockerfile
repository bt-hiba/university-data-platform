# ─────────────────────────────────────────────────────────────────────────────
# Image Airflow custom — ajoute Playwright (Chromium) au worker pour le
# tier 3 du crawler (rendu des Single Page Applications).
#
# Couche libs système avant pip pour que la cache Docker reste efficace.
# ─────────────────────────────────────────────────────────────────────────────
FROM apache/airflow:2.10.4-python3.11

USER root

# Dépendances système requises par Chromium headless
RUN apt-get update && apt-get install -y --no-install-recommends \
        libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
        libxkbcommon0 libatspi2.0-0 libxcomposite1 libxdamage1 \
        libxrandr2 libxfixes3 libgbm1 libpango-1.0-0 libcairo2 libasound2 \
        libxshmfence1 fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Dépendances Python du projet + Playwright
RUN pip install --no-cache-dir \
        requests minio python-dotenv loguru pyyaml pymupdf \
        beautifulsoup4 lxml playwright

# Télécharge le binaire Chromium dans l'image (sinon il faudrait le faire
# à chaque démarrage du container)
RUN playwright install chromium
