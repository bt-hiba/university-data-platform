# University Data Platform

## Description
Projet de plateforme de données universitaires basé sur ingestion, transformation et stockage.

🚀 Étape 1 : Mise en place de MinIO et test d’ingestion
Cette étape consiste à mettre en place un stockage local avec MinIO et à valider l’upload de fichiers via Python.

✔️ 1. Préparation de l’environnement
Installation et configuration de Docker
Mise en place d’un environnement de développement stable

✔️ 2. Déploiement de MinIO
Configuration via docker-compose.yml
Lancement du service dans Docker
Vérification de l’interface MinIO

✔️ 3. Configuration des buckets
Création des buckets :
raw-web-html, raw-documents, raw-json, raw-logs
Automatisation via script Python

✔️ 4. Connexion Python → MinIO
Installation du SDK MinIO
Configuration du client (minio_client.py)
Test de connexion réussi

✔️ 5. Test d’upload
Création d’un fichier test
Script d’upload Python
Upload réussi vers MinIO

🎯 Résultat
Une infrastructure MinIO fonctionnelle permettant :
gestion des buckets
upload de fichiers via Python
base d’un pipeline d’ingestion de données
