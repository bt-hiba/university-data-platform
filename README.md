# University Data Platform

## Description
Plateforme d'ingestion de données universitaires construite autour d'une **Raw Zone** immuable (MinIO) et orchestrée par **Apache Airflow**. La Semaine 1 livre un pipeline d'ingestion quotidien couvrant trois sources : web (crawler récursif), API (OpenAlex) et fichiers locaux (CSV/JSON/PDF).

## Architecture (Semaine 1)

```
                   ┌─────────────────────────────────────┐
                   │   Airflow (Webserver / Scheduler /  │
                   │            Worker Celery)           │
                   └────────────────┬────────────────────┘
                                    │  DAG : daily_ingestion
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
  crawl_website                collect_api                collect_files
  (BFS récursif)               (OpenAlex)                 (CSV/JSON/PDF)
        │                           │                           │
        └─────────────┬─────────────┴─────────────┬─────────────┘
                      ▼                           ▼
              ┌───────────────┐           ┌───────────────┐
              │  raw-html     │           │ raw-json      │
              │  raw-documents│           │ raw-logs      │
              └───────────────┘           └───────────────┘
                          MinIO (Raw Zone)
```

Conteneurs définis dans `docker-compose.yml` :
- `postgres` (métadonnées Airflow)
- `redis` (broker Celery)
- `minio` (stockage S3-compatible, console sur :9001)
- `airflow-init` (création de l'utilisateur admin)
- `airflow-webserver` (UI sur :8080)
- `airflow-scheduler`
- `airflow-worker`

## Prérequis
- Docker Desktop ≥ 24.x (WSL2 sous Windows)
- 4 GB RAM disponibles pour la stack
- Ports libres : `5432`, `6379`, `8080`, `9000`, `9001`

## Démo end-to-end (Semaine 1)

### 1. Démarrer la stack
```powershell
docker compose up -d
```
La première initialisation prend 3–5 min (init DB Airflow + install des `_PIP_ADDITIONAL_REQUIREMENTS`). Vérifier que tout est `healthy` :
```powershell
docker compose ps
```

### 2. Accéder aux UIs
| Service        | URL                       | Credentials             |
|----------------|---------------------------|-------------------------|
| Airflow        | http://localhost:8080     | `admin` / `admin`       |
| MinIO console  | http://localhost:9001     | `minioadmin` / `minioadmin` |

### 3. Déclencher le DAG
Depuis l'UI Airflow : activer le toggle du DAG `daily_ingestion` puis cliquer sur *Trigger DAG*.
Ou en CLI :
```powershell
docker compose exec airflow-scheduler airflow dags unpause daily_ingestion
docker compose exec airflow-scheduler airflow dags trigger daily_ingestion
```

Pipeline exécuté :
```
start → ensure_buckets → [crawl_website | collect_api | collect_files] → save_metadata → finish
```

### 4. Vérifier les artefacts dans MinIO
```powershell
docker compose exec minio mc alias set local http://localhost:9000 minioadmin minioadmin
docker compose exec minio mc ls --recursive local/raw-html
docker compose exec minio mc ls --recursive local/raw-json
docker compose exec minio mc ls --recursive local/raw-documents
docker compose exec minio mc ls --recursive local/raw-logs
```

Structure attendue :
```
raw-html/source=<src>/year=YYYY/month=MM/day=DD/1.html
raw-html/source=<src>/year=YYYY/month=MM/day=DD/1-1.html
raw-html/source=<src>/year=YYYY/month=MM/day=DD/1-1-2.html
raw-documents/source=<src>/.../1-3-2.pdf
raw-json/source=openalex/.../page_1.json
raw-logs/source=<src>/.../metadata_<node_id>.json
raw-logs/source=pipeline/.../run_summary_<run_id>.json
```

## Convention de nommage `node_id`

Le crawler attribue un identifiant hiérarchique générique à chaque page/document découvert :
- Racine : `1`
- Enfants de `1` : `1.1`, `1.2`, `1.3`…
- Petits-enfants de `1.1` : `1.1.1`, `1.1.2`…

Le `node_id` est utilisé comme nom de fichier (avec `-` au lieu de `.`) :
- `1.html`, `1-1.html`, `1-1-2.pdf`

Chaque objet possède un **sidecar JSON** dans `raw-logs` contenant : `node_id`, `parent_id`, `depth`, `source_url`, `content_hash` (SHA-256), `crawl_timestamp`, `http_status`.

## Configuration (`.env`)

| Variable | Défaut | Rôle |
|----------|--------|------|
| `CRAWLER_ROOT_URL`        | `https://fsac.ac.ma` | URL racine du crawl |
| `CRAWLER_SOURCE_NAME`     | `fsac`               | Nom de partition dans MinIO |
| `CRAWLER_MAX_DEPTH`       | `3`                  | Profondeur maximale BFS |
| `CRAWLER_MAX_PAGES`       | `30`                 | Plafond de pages crawlées |
| `CRAWLER_REQUEST_TIMEOUT` | `30`                 | Timeout HTTP (s) |
| `MINIO_ENDPOINT`          | `minio:9000`         | Endpoint interne (containers) |
| `MINIO_ENDPOINT_LOCAL`    | `localhost:9000`     | Endpoint hôte (tests locaux) |

Toute modification du `.env` nécessite un redémarrage :
```powershell
docker compose up -d --force-recreate airflow-worker airflow-scheduler
```

## Filtre OpenAlex
Configuré dans `configs/sources.yaml` :
```yaml
query_params:
  filter: "institutions.country_code:ma,type:article"
  sort:   "publication_date:desc"
pagination:
  per_page: 50
  max_pages: 2
```
→ Publications d'institutions marocaines, 2 pages × 50 résultats.

## Fichiers locaux d'exemple
`ingestion/files/sample_data/` contient un échantillon générique (`courses.csv`, `faculties.json`, `guide.pdf`) ingéré vers `raw-documents` / `raw-json` à chaque run.

## Tests
```powershell
python -m pytest tests/ -v
```

## Limitation connue — `fsac.ac.ma`
La cible par défaut (`fsac.ac.ma`) est une **Single Page Application** : les liens du menu (`annonces.html`, `events.html`, `tabs.html?page=formations`) sont gérés en JavaScript côté client et renvoient `404` côté serveur. Le crawler les **découvre correctement** (voir logs : `node=1.1 url=…/annonces.html`) mais ne peut pas les télécharger.

Pour valider visuellement l'arborescence multi-niveaux dans MinIO, changer temporairement la racine dans `.env` :
```env
CRAWLER_ROOT_URL=https://www.python.org
CRAWLER_SOURCE_NAME=pythonorg_demo
```
puis relancer le DAG. Résultat attendu : `1.html`, `1-1.html`, …, `1-14.html` dans `raw-html/source=pythonorg_demo/…`.

## Arrêt
```powershell
docker compose down            # garde les volumes (MinIO + Postgres)
docker compose down -v         # supprime aussi les données
```

---

## Historique des étapes Semaine 1

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

📦 Étape 4 – File Ingestion (Pipeline d’ingestion des fichiers)
🎯 Objectif

L’étape 4 constitue le point d’entrée des données dans le Data Lake.
Elle permet l’ingestion automatique des fichiers locaux (CSV, JSON, PDF) vers MinIO (Raw Zone) après traitement.

🔁 Vue globale du pipeline
Fichiers (CSV / JSON / PDF)
        ↓
Lecture des données
        ↓
Génération de métadonnées
        ↓
Logging des opérations
        ↓
Calcul du hash
        ↓
Upload vers MinIO
⚙️ Fonctionnement général

Le pipeline d’ingestion est responsable de :

détecter le type de fichier
lire et extraire son contenu
générer des métadonnées (type, taille, timestamp, hash)
enregistrer les événements via logging
assurer l’intégrité des fichiers avec un hash
transférer les fichiers vers MinIO
📂 Types de fichiers supportés
CSV : données tabulaires structurées
JSON : données semi-structurées
PDF : extraction de texte brut
🧾 Métadonnées

Chaque fichier ingéré est enrichi automatiquement avec :

nom du fichier
type de source
taille
hash de contenu
date et heure d’ingestion

🎯 Elles assurent la traçabilité, le suivi et la détection de doublons.

🪵 Logging

Toutes les étapes du pipeline sont journalisées :

début d’ingestion
succès de lecture
génération des métadonnées
upload vers MinIO
gestion des erreurs

🎯 Objectif : assurer la transparence et faciliter le débogage.

☁️ Stockage MinIO (Raw Zone)

Les fichiers sont stockés dans MinIO selon une structure organisée :

classification par type (CSV, JSON, PDF)
organisation temporelle (année/mois/jour)

🎯 Cela permet une gestion efficace du Data Lake et une meilleure exploitation des données.

🧪 Résultat attendu

À l’exécution du pipeline :

les fichiers sont correctement ingérés
les métadonnées sont générées
les logs sont enregistrés
les fichiers sont stockés dans MinIO
✅ Conclusion

L’étape 4 assure une ingestion fiable, traçable et structurée des données vers le Data Lake, constituant une base solide pour les étapes de traitement et d’analyse ultérieures.

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


#Pour le test de spark:
 docker exec spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --conf spark.executor.extraClassPath=/opt/spark/jars/hadoop-aws-3.3.4.jar:/opt/spark/jars/aws-java-sdk-bundle-1.12.262.jar --conf spark.driver.extraClassPath=/opt/spark/jars/hadoop-aws-3.3.4.jar:/opt/spark/jars/aws-java-sdk-bundle-1.12.262.jar /opt/spark-apps/test_connection.py

 Analyse le projet university-data-platform et mets à jour le README pour refléter l’état actuel du projet après les ajouts de la Semaine 2.

Contexte général :
Le projet est une plateforme de données universitaires basée sur :
- Airflow pour l’orchestration
- MinIO pour la Raw Zone
- Docker Compose pour l’infrastructure
- Spark pour la transformation et la lecture des données brutes avant Hudi

Ce qui était déjà fait en Semaine 1 :
- Pipeline Airflow daily_ingestion fonctionnel
- Ingestion web via crawler
- Ingestion API OpenAlex
- Ingestion fichiers CSV / JSON / PDF
- Stockage dans MinIO avec buckets :
  - raw-html
  - raw-json
  - raw-documents
  - raw-logs
- Génération de métadonnées
- Logs, timestamps, hashes SHA-256
- Tests unitaires pour ingestion et utils

Ce qui a été ajouté / corrigé récemment :

1. Ajout de Spark dans Docker Compose
Deux services Spark sont maintenant définis :
- spark-master
- spark-worker

Le master expose :
- Spark UI : http://localhost:8081
- Spark master URL : spark://spark-master:7077

Les services Spark utilisent l’image :
- apache/spark:3.5.1

Commandes configurées :
- spark-master lance :
  /opt/spark/bin/spark-class org.apache.spark.deploy.master.Master

- spark-worker lance :
  /opt/spark/bin/spark-class org.apache.spark.deploy.worker.Worker spark://spark-master:7077

Les deux services sont connectés au réseau :
- university-network

2. Ajout des JARs nécessaires pour lire MinIO avec Spark S3A
Les JARs sont dans :
- spark/jars/hadoop-aws-3.3.4.jar
- spark/jars/aws-java-sdk-bundle-1.12.262.jar

Important :
On ne monte pas tout le dossier spark/jars vers /opt/spark/jars, car cela écrase les JARs internes de Spark.
On monte les deux JARs fichier par fichier :
- ./spark/jars/hadoop-aws-3.3.4.jar:/opt/spark/jars/hadoop-aws-3.3.4.jar
- ./spark/jars/aws-java-sdk-bundle-1.12.262.jar:/opt/spark/jars/aws-java-sdk-bundle-1.12.262.jar

3. Création / stabilisation de spark_session.py
Le fichier spark/spark_session.py crée une SparkSession compatible avec :
- Spark master Docker : spark://spark-master:7077
- MinIO via S3A : minio:9000
- credentials MinIO : minioadmin / minioadmin

Le fichier utilise les variables .env quand elles existent :
- SPARK_MASTER
- MINIO_ENDPOINT
- MINIO_ACCESS_KEY
- MINIO_SECRET_KEY

Il contient aussi des valeurs par défaut pour fonctionner dans les conteneurs Docker.

4. Test de connexion Spark
Le fichier spark/test_connection.py permet de tester que Spark master et worker fonctionnent.

Commande :
docker exec spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 /opt/spark-apps/test_connection.py

Résultat attendu :
Spark Version:
3.5.1
Rows: 2

Et affichage d’un DataFrame avec :
- Ahmed / CS
- Fatima / Math

Validation obtenue :
- Spark master fonctionne
- Spark worker fonctionne
- Le worker est enregistré dans le master
- Spark UI affiche Status: ALIVE
- Spark UI affiche Alive Workers: 1
- Un job PySpark s’exécute correctement sur le cluster

5. Ajout du test de lecture MinIO avant Hudi
Nouveau fichier :
- spark/read_minio.py

Objectif :
Tester que Spark peut lire les données brutes depuis MinIO avant de passer à Hudi.

Par défaut, il lit :
s3a://raw-json/

Il lit en format text par défaut, car le bucket raw-json contient plusieurs fichiers JSON bruts avec des structures différentes. Une lecture directe en JSON peut échouer à cause de conflits de colonnes Spark.

Commande :
docker exec spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 /opt/spark-apps/read_minio.py

Résultat obtenu :
Reading MinIO path: s3a://raw-json/
Format: text
Rows: 213792

Cela valide :
- Spark arrive à se connecter à MinIO
- Spark arrive à lire depuis s3a://raw-json/
- Les JARs S3A fonctionnent
- Le worker exécute les tâches Spark

Option avancée :
Pour tester un chemin précis :
docker exec -e READ_MINIO_PATH=s3a://raw-json/source=openalex/ spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 /opt/spark-apps/read_minio.py

Pour forcer une lecture JSON :
docker exec -e READ_MINIO_FORMAT=json spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 /opt/spark-apps/read_minio.py

6. Correction Airflow init
Problème rencontré :
Airflow UI répondait avec ERR_EMPTY_RESPONSE sur http://localhost:8080.

Cause :
Le service airflow-init n’était pas connecté au réseau university-network, donc il ne pouvait pas résoudre le host postgres. La base metadata Airflow n’était donc pas initialisée.

Correction dans docker-compose.yml :
Ajouter à airflow-init :
networks:
  - university-network

Après correction :
docker compose up airflow-init
docker compose up -d airflow-webserver airflow-scheduler airflow-worker

Résultat :
- Airflow webserver healthy
- Airflow scheduler healthy
- Metadata database healthy
- http://localhost:8080 répond 200
- Login : admin / admin

7. Correction MinIO non démarré
Problème rencontré dans Airflow :
La tâche ensure_buckets échouait ou restait en retry.

Cause :
MinIO n’était pas lancé.

Correction :
docker compose up -d minio

Vérification :
docker ps --filter "name=minio"

Résultat attendu :
university-minio Up ... healthy

Après démarrage MinIO :
- ensure_buckets passe en success
- crawl_website passe en success
- collect_api passe en success
- collect_files passe en success
- save_metadata passe en success
- finish passe en success
- Le DAG daily_ingestion manuel passe en success

8. Commande recommandée pour démarrer toute l’infrastructure
Ajouter dans le README :

docker compose up -d postgres redis minio airflow-webserver airflow-scheduler airflow-worker spark-master spark-worker

Puis vérifier :
docker ps

URLs :
- Airflow : http://localhost:8080
- Spark Master UI : http://localhost:8081
- MinIO Console : http://localhost:9001

Credentials :
- Airflow : admin / admin
- MinIO : minioadmin / minioadmin

9. Commandes de diagnostic utiles
Airflow :
docker logs --tail 80 university-airflow-webserver
docker logs --tail 80 university-airflow-scheduler
docker logs --tail 80 university-airflow-worker

MinIO :
docker logs --tail 80 university-minio

Spark :
docker logs --tail 80 spark-master
docker logs --tail 80 spark-worker

Vérifier Spark :
docker ps --filter "name=spark"

Relancer Spark :
docker compose up -d spark-master spark-worker

10. État actuel avant Hudi
Le projet est prêt pour l’étape suivante Hudi parce que :
- Airflow fonctionne
- MinIO fonctionne
- Les buckets raw existent
- Le DAG daily_ingestion fonctionne
- Spark master et worker fonctionnent
- Spark lit MinIO via s3a://
- Le test read_minio.py valide la lecture de raw-json
- Les fichiers Hudi futurs existent déjà comme placeholders :
  - spark/hudi_writer.py
  - spark/quality_checks.py
  - spark/transform_faculty_profiles.py
  - spark/transform_course_catalog.py

Prochaine étape recommandée :
Implémenter l’écriture Hudi dans spark/hudi_writer.py, puis construire les transformations :
- faculty_profiles
- course_catalog

Mettre à jour le README avec une section “Semaine 2 - Spark + MinIO validation” contenant :
- architecture Spark
- commandes de démarrage
- commandes de test Spark
- commandes de test lecture MinIO
- problèmes rencontrés et corrections
- état validé avant Hudi
