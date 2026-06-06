# University Data Platform

## Description
Projet de plateforme de données universitaires basé sur ingestion, transformation et stockage.

## Description des étapes réalisées durant la première semaine

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








🚀 Étape 5 : Logs, Hash et Timestamps — Utils
Cette étape consiste à développer les utilitaires communs utilisés par les différents modules d’ingestion du projet.

✔️ 1. `utils/time_utils.py`

Gestion des dates et timestamps :

* génération de timestamps au format ISO 8601 ;
* récupération de l’année, du mois et du jour ;
* génération automatique des chemins de stockage MinIO (`source=xxx/year=YYYY/month=MM/day=DD`).

✔️ 2.`utils/hash_utils.py`

Calcul des empreintes SHA-256 :

* hash de fichiers ;
* hash de texte (HTML, JSON, etc.) ;
* hash de données binaires (bytes) ;
* lecture par blocs pour les fichiers volumineux.

✔️ 3. `utils/logger.py`

Mise en place du système de journalisation :

* logs dans la console et dans un fichier ;
* rotation automatique des fichiers de logs ;
* conservation des logs pendant 7 jours ;
* fonctions dédiées au suivi des opérations d’ingestion (démarrage, succès, erreurs, retries et métadonnées).

✔️ 4.`utils/__init__.py`

Déclaration du package Python pour faciliter les imports dans le projet.

✔️ 5. Tests

Création de `tests/test_utils.py` pour valider le bon fonctionnement des trois modules.

---

🎯 Résultat

Un ensemble d’utilitaires réutilisables permettant :

* de générer des timestamps et chemins de stockage cohérents ;
* de calculer des empreintes pour la traçabilité et la déduplication ;
* de journaliser les opérations du pipeline de manière fiable.

