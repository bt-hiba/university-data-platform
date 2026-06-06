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



🚀 Étape 2 : API Ingestion — OpenAlex

Cette étape consiste à développer le module d’ingestion de données depuis des APIs externes, avec OpenAlex comme première source de données académiques.

✔️ 1. Configuration des sources API

Création du fichier `configs/sources.yaml` permettant de centraliser la configuration des APIs :

* URL de base ;
* endpoints ;
* timeout ;
* nombre maximal de tentatives (retries) ;
* paramètres de pagination.

✔️ 2. Connecteur API générique

Développement du module `ingestion/api/api_connector.py` :

* chargement automatique de la configuration depuis `sources.yaml` ;
* exécution des requêtes HTTP GET avec la bibliothèque `requests` ;
* gestion des timeouts ;
* gestion des erreurs réseau ;
* mécanisme de retry automatique ;
* prise en charge de la pagination.

✔️ 3. Connecteur OpenAlex

Développement du module `ingestion/api/openalex_connector.py` :

* connexion à l’API OpenAlex ;
* récupération des publications scientifiques ;
* normalisation des données retournées ;
* exposition de la méthode `fetch_publications()`.

✔️ 4. Pipeline d’ingestion API

Développement du module `ingestion/api/api_ingestor.py` :

* récupération des données depuis OpenAlex ;
* sauvegarde locale des données brutes au format JSON ;
* calcul d’empreintes SHA-256 pour la traçabilité ;
* génération automatique des métadonnées ;
* upload des fichiers JSON vers MinIO ;
* création automatique des partitions de stockage.

Structure de stockage utilisée :

raw-json/source=openalex/year=YYYY/month=MM/day=DD/

✔️ 5. Métadonnées d’ingestion

Génération automatique des métadonnées suivantes :

* source_system ;
* source_url ;
* ingestion_timestamp ;
* content_hash ;
* record_count ;
* status.

✔️ 6. Journalisation et gestion des erreurs

Intégration du système de logs commun du projet :

* journalisation des opérations d’ingestion ;
* suivi des erreurs HTTP ;
* gestion des erreurs de connexion ;
* gestion des timeouts ;
* journalisation des tentatives de retry ;
* suivi des opérations de stockage.

✔️ 7. Tests

Création du fichier `tests/test_ingestion.py` permettant de valider :

* la génération des hashes SHA-256 ;
* la création des chemins partitionnés ;
* la génération des métadonnées ;
* la sauvegarde locale des fichiers JSON ;
* l’upload vers MinIO ;
* le pipeline complet d’ingestion OpenAlex.

Contribution d'intégration :
Création et configuration du fichier .env contenant les paramètres de connexion MinIO
nécessaires à l'exécution et aux tests du pipeline d'ingestion.

🎯 Résultat

Un module d’ingestion API robuste permettant :

* de collecter automatiquement des données académiques depuis OpenAlex ;
* de stocker les données brutes dans une architecture partitionnée ;
* d’assurer la traçabilité grâce aux métadonnées et aux empreintes SHA-256 ;
* d’intégrer les données au Data Lake via MinIO ;
* de disposer d’un pipeline d’ingestion extensible pour d’autres APIs futures.




🚀 Étape 3 : Web Scraping — Pages HTML universitaires

Cette étape consiste à développer le module de scraping web pour collecter 
les pages HTML des universités, avec gestion des erreurs, traçabilité et 
stockage dans le Data Lake.

✔️ 1. Configuration des sources web

Ajout de la section `universities` dans `configs/sources.yaml` permettant 
de centraliser la liste des universités à scraper :

* nom de la source ;
* URL de la page principale.

✔️ 2. Pipeline de scraping web

Développement du module `ingestion/web/scraper_requests.py` :

* lecture automatique de la liste des universités depuis `sources.yaml` ;
* téléchargement des pages HTML avec la bibliothèque `requests` ;
* gestion des timeouts ;
* gestion des erreurs réseau et HTTP ;
* mécanisme de retry automatique (3 tentatives) ;
* en-têtes HTTP simulant un navigateur réel.

✔️ 3. Traçabilité et intégrité

* calcul d'empreintes SHA-256 sur le contenu HTML brut ;
* horodatage ISO 8601 de chaque ingestion ;
* sauvegarde locale organisée par date.

✔️ 4. Métadonnées d'ingestion

Génération automatique des métadonnées suivantes :

* source_name ;
* source_type ;
* url ;
* ingested_at ;
* pipeline ;
* hash_sha256 ;
* hash_algorithm ;
* local_path ;
* minio_bucket ;
* minio_object.

✔️ 5. Stockage dans MinIO

Upload automatique des fichiers HTML vers le bucket `raw-web-html` :

Structure de stockage utilisée :

raw-web-html/source=nom/year=YYYY/month=MM/day=DD/

✔️ 6. Journalisation et gestion des erreurs

Intégrati



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

