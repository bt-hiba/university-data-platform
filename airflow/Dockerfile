# ─────────────────────────────────────────────────────────────────────────────
# Image Airflow custom — ajoute Playwright (Chromium) au worker pour le
# tier 3 du crawler (rendu des Single Page Applications).
#
# Couche libs système avant pip pour que la cache Docker reste efficace.
# ─────────────────────────────────────────────────────────────────────────────
FROM apache/airflow:2.10.4-python3.11

USER root

# Dépôt Adoptium pour un JDK 11 à jour (absent des dépôts Debian bookworm)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl gnupg ca-certificates \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://packages.adoptium.net/artifactory/api/gpg/key/public \
        | gpg --dearmor -o /etc/apt/keyrings/adoptium.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/adoptium.gpg] https://packages.adoptium.net/artifactory/deb $(awk -F= '/^VERSION_CODENAME/{print $2}' /etc/os-release) main" \
        > /etc/apt/sources.list.d/adoptium.list \
    && apt-get update && apt-get install -y --no-install-recommends \
        temurin-11-jre \
        procps \
        libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
        libxkbcommon0 libatspi2.0-0 libxcomposite1 libxdamage1 \
        libxrandr2 libxfixes3 libgbm1 libpango-1.0-0 libcairo2 libasound2 \
        libxshmfence1 fonts-liberation \
    && rm -rf /var/lib/apt/lists/*
# Client Spark uniquement : les exécuteurs restent sur le cluster Spark
# existant et les JARs Hudi/S3A sont fournis par docker-compose.
ARG SPARK_VERSION=3.5.1
RUN curl -fsSL "https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz" \
    | tar -xz -C /opt \
    && ln -s "/opt/spark-${SPARK_VERSION}-bin-hadoop3" /opt/spark \
    && chown -R airflow:root "/opt/spark-${SPARK_VERSION}-bin-hadoop3"

ENV JAVA_HOME=/usr/lib/jvm/temurin-11-jre-amd64 \
    SPARK_HOME=/opt/spark \
    PATH=/opt/spark/bin:${PATH}
USER airflow

RUN ls /usr/lib/jvm/

# Dépendances Python du projet + Playwright
RUN pip install --no-cache-dir \
        requests minio python-dotenv loguru pyyaml pymupdf \
        beautifulsoup4 lxml playwright elasticsearch==8.15.1

# Télécharge le binaire Chromium dans l'image (sinon il faudrait le faire
# à chaque démarrage du container)
RUN playwright install chromium
