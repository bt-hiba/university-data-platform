FROM apache/spark:3.5.1

USER root

ARG PYTHON_VERSION=3.11.9

# Airflow utilise Python 3.11. PySpark exige la même version mineure pour
# le driver et les workers, alors que l'image Spark 3.5.1 fournit Python 3.8.
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        build-essential ca-certificates curl \
        libbz2-dev libffi-dev libgdbm-dev liblzma-dev libncursesw5-dev \
        libreadline-dev libsqlite3-dev libssl-dev uuid-dev zlib1g-dev \
    && curl -fsSL "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz" \
        -o /tmp/python.tgz \
    && tar -xzf /tmp/python.tgz -C /tmp \
    && cd "/tmp/Python-${PYTHON_VERSION}" \
    && ./configure --with-ensurepip=install \
    && make -j"$(nproc)" altinstall \
    && rm -rf /tmp/python.tgz "/tmp/Python-${PYTHON_VERSION}" /var/lib/apt/lists/*

ENV PYSPARK_PYTHON=/usr/local/bin/python3.11

RUN python3.11 -m pip install --no-cache-dir \
    elasticsearch==8.14.0 \
    requests

USER spark
