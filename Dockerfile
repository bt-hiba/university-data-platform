FROM python:3.10-slim

WORKDIR /opt

# Copie requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie uniquement le dossier api et les fichiers nécessaires
COPY api/ ./api/

EXPOSE 8000