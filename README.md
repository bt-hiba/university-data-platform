# University Data Platform

Plateforme de données universitaires conteneurisée. Elle collecte des données
brutes, les transforme en tables analytiques, les rend consultables dans un
moteur de recherche et les expose via une API et un tableau de bord.

> Ce fichier est une proposition de README réorganisé. Le fichier `README.md`
> existant n'est pas modifié.

## Vue d'ensemble

Le projet couvre tout le flux de données :

```text
Sources universitaires
  ├─ Site web (crawler, compatible SPA)
  ├─ OpenAlex (API)
  └─ Fichiers locaux (CSV, JSON, PDF)
             │
             ▼
Airflow : orchestration du DAG `daily_ingestion`
             │
             ▼
MinIO : zone brute (Raw Zone)
             │
             ▼
Spark + Hudi : transformations parallèles
             │
             ▼
Hive : métastore et requêtes SQL
        ┌────┴─────┐
        ▼          ▼
Elasticsearch    Metabase
        │
        ▼
FastAPI : API de recherche
```

## Fonctionnalités

- Ingestion quotidienne orchestrée avec Apache Airflow.
- Collecte web récursive avec prise en charge des sites dynamiques.
- Collecte de publications académiques depuis OpenAlex.
- Ingestion de fichiers CSV, JSON et PDF.
- Exécution parallèle des tâches indépendantes d'ingestion, de transformation Spark et d'indexation Elasticsearch.
- Stockage brut dans MinIO, avec partitionnement par source et par date.
- Métadonnées, journaux et empreintes SHA-256 pour la traçabilité.
- Transformations distribuées avec Spark et écriture de tables Apache Hudi.
- Enregistrement des tables Hudi dans Hive.
- Indexation des profils et cours dans Elasticsearch.
- API REST FastAPI et documentation Swagger.
- Visualisation des données avec Metabase.

## Architecture technique

| Couche | Technologies | Rôle |
|---|---|---|
| Orchestration | Airflow, Redis, PostgreSQL | Exécute et planifie le pipeline. |
| Raw Zone | MinIO | Stocke les données brutes et les métadonnées. |
| Traitement | Spark 3.5.1, Hudi 0.15.0 | Transforme les données et produit les tables curées. |
| Métadonnées SQL | Hive 4.0.0, PostgreSQL | Catalogue les tables Hudi et les rend requêtables. |
| Recherche | Elasticsearch 8.15.0, Kibana | Indexe les données curées et fournit la recherche textuelle. |
| API | FastAPI | Expose les recherches via HTTP. |
| BI | Metabase | Crée les analyses et tableaux de bord. |

Tous les conteneurs communiquent sur le réseau Docker `university-network`.

## Structure du projet

```text
airflow/                 # Image Airflow et DAGs
  dags/daily_ingestion_dag.py
api/                     # API FastAPI de recherche
configs/                 # Configuration des sources et de MinIO
dashboard/               # Requêtes et captures Metabase
hive/                    # Configuration Hive et enregistrement des tables
ingestion/               # Connecteurs web, API et fichiers locaux
search/                  # Création d'index et recherche Elasticsearch
spark/                   # Session Spark, transformations et écriture Hudi
storage/                 # Client MinIO et gestion des buckets
tests/                   # Tests unitaires
utils/                   # Hashes, dates et journalisation
docker-compose.yml       # Infrastructure complète
```

## Prérequis

- Docker Desktop récent, avec Docker Compose v2.
- Au moins 8 Go de mémoire disponibles pour l'ensemble des services.
- Ports disponibles : `3000`, `5432`, `7077`, `8000`, `8080`, `8081`, `9000`,
  `9001`, `9083`, `9200`, `5601`, `10000` et `10001`.
- Python 3 pour lancer les tests unitaires depuis l'hôte (facultatif).

Créez et renseignez le fichier `.env` à partir des variables utilisées par
`docker-compose.yml`. Les variables importantes sont :

```env
POSTGRES_USER=airflow
POSTGRES_PASSWORD=airflow
POSTGRES_DB=airflow

MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false

SPARK_MASTER=spark://spark-master:7077

CRAWLER_ROOT_URL=https://fsac.ac.ma
CRAWLER_SOURCE_NAME=fsac
CRAWLER_MAX_DEPTH=3
CRAWLER_MAX_PAGES=30
CRAWLER_REQUEST_TIMEOUT=30
CRAWLER_ENABLE_PLAYWRIGHT=true
```

## Démarrage

Depuis la racine du projet, lancez toute l'infrastructure :

```powershell
docker compose up -d --build
```

Lors du premier démarrage, attendez que les services d'initialisation Airflow
et Hive aient terminé, puis contrôlez l'état des conteneurs :

```powershell
docker compose ps
docker ps
```

Pour démarrer seulement les services essentiels au pipeline, utilisez :

```powershell
docker compose up -d postgres redis minio airflow-webserver airflow-scheduler airflow-worker spark-master spark-worker
```

## Interfaces disponibles

| Service | Adresse | Accès |
|---|---|---|
| Airflow | http://localhost:8080 | `admin` / `admin` |
| MinIO Console | http://localhost:9001 | variables `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` |
| Spark Master UI | http://localhost:8081 | — |
| Metabase | http://localhost:3000 | configuration au premier accès ou volume restauré |
| Elasticsearch | http://localhost:9200 | sécurité désactivée pour l'environnement local |
| Kibana | http://localhost:5601 | — |
| API FastAPI | http://localhost:8000 | — |
| Swagger / OpenAPI | http://localhost:8000/docs | — |
| HiveServer2 | `localhost:10000` | JDBC / Beeline |
| Spark Thrift Server | `localhost:10001` | JDBC |

## Pipeline Airflow

Le DAG `daily_ingestion` est planifié quotidiennement et peut aussi être
déclenché manuellement depuis l'interface Airflow.

Il utilise une stratégie d'exécution hybride parallèle : les tâches
indépendantes sont exécutées simultanément, tandis que les dépendances entre
les différentes étapes sont conservées.

```text
                         start
                           |
                     ensure_buckets
                           |
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
       crawl_website  collect_api  collect_files
             │             │             │
             └─────────────┼─────────────┘
                           |
                     save_metadata
                           |
                ┌──────────┴──────────┐
                ▼                     ▼
       transform_faculty       transform_courses
                │                     │
                └──────────┬──────────┘
                           |
                  register_hudi_tables
                           |
                ┌──────────┴──────────┐
                ▼                     ▼
           index_faculty        index_courses
                │                     │
                └──────────┬──────────┘
                           |
                         finish

Déclenchement en ligne de commande :

```powershell
docker compose exec airflow-scheduler airflow dags unpause daily_ingestion
docker compose exec airflow-scheduler airflow dags trigger daily_ingestion
```

### Données brutes dans MinIO

| Bucket | Contenu |
|---|---|
| `raw-html` | Pages HTML collectées par le crawler. |
| `raw-json` | Résultats OpenAlex et fichiers JSON. |
| `raw-documents` | Documents et fichiers locaux, dont PDF et CSV. |
| `raw-logs` | Sidecars de métadonnées et résumés de pipeline. |

Les objets sont partitionnés selon une convention similaire à :

```text
raw-json/source=openalex/year=YYYY/month=MM/day=DD/page_1.json
raw-html/source=fsac/year=YYYY/month=MM/day=DD/1-1.html
raw-logs/source=pipeline/year=YYYY/month=MM/day=DD/run_summary_<run_id>.json
```

Chaque ingestion produit des métadonnées telles que l'horodatage, la source,
le chemin, le statut, le nombre d'enregistrements et l'empreinte SHA-256.

## Spark et lecture de MinIO

Le cluster est composé d'un master et d'un worker Spark. Le master est
accessible à l'adresse `spark://spark-master:7077`.

Les JARs `hadoop-aws`, `aws-java-sdk-bundle` et Hudi sont montés individuellement
dans les conteneurs. Il ne faut pas monter tout le répertoire des JARs sur
`/opt/spark/jars`, car cela remplacerait les dépendances internes de Spark.

Vérifiez le cluster avec :

```powershell
docker exec spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 /opt/spark-apps/test_connection.py
```

Le test doit afficher la version de Spark, un DataFrame d'exemple et `Rows: 2`.

Vérifiez ensuite la lecture des données brutes depuis MinIO :

```powershell
docker exec spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 /opt/spark-apps/read_minio.py
```

Par défaut, ce test lit `s3a://raw-json/` au format `text`, ce qui évite les
conflits de schéma entre fichiers JSON bruts hétérogènes. Pour choisir un chemin
ou un format précis :

```powershell
docker exec -e READ_MINIO_PATH=s3a://raw-json/source=openalex/ spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 /opt/spark-apps/read_minio.py
docker exec -e READ_MINIO_FORMAT=json spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 /opt/spark-apps/read_minio.py
```

## Transformations Hudi et Hive

Les transformations produisent les tables curées `faculty_profiles` et
`course_catalog`. Elles peuvent être exécutées indépendamment :

```powershell
docker exec spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 /opt/spark-apps/transform_faculty_profiles.py
docker exec spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 /opt/spark-apps/transform_course_catalog.py
```

Puis enregistrez les tables Hudi dans Hive :

```powershell
docker exec spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 /opt/spark-apps/register_hudi_tables.py
```

Pour vérifier les tables et leurs contenus :

```powershell
docker compose exec spark-master /bin/sh -lc '/opt/spark/bin/spark-sql --master spark://spark-master:7077 --conf spark.hadoop.hive.metastore.uris=thrift://hive-metastore:9083 --conf spark.sql.catalogImplementation=hive -e "SHOW TABLES;"'
docker compose exec spark-master /bin/sh -lc '/opt/spark/bin/spark-sql --master spark://spark-master:7077 --conf spark.hadoop.hive.metastore.uris=thrift://hive-metastore:9083 --conf spark.sql.catalogImplementation=hive -e "SELECT COUNT(*) FROM faculty_profiles; SELECT COUNT(*) FROM course_catalog;"'
```

## Elasticsearch et API de recherche

Après la création des tables Hudi, créez les index puis alimentez-les :

```powershell
docker compose up -d elasticsearch kibana api-server
docker compose exec spark-master python3 /opt/search/test_connection.py
docker compose exec spark-master python3 /opt/search/create_indices.py
docker compose exec spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 /opt/search/index_faculty.py
docker compose exec spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 /opt/search/index_courses.py
docker compose exec spark-master python3 /opt/search/test_search.py
```

Contrôles HTTP rapides :

```powershell
curl http://localhost:9200/_cat/indices?v
curl http://localhost:9200/faculty_profiles/_count
curl http://localhost:9200/course_catalog/_count
```

L'API propose notamment les routes suivantes :

| Route | Rôle |
|---|---|
| `GET /` | Vérification de disponibilité de l'API. |
| `GET /search/faculty` | Recherche dans les profils d'enseignants. |
| `GET /search/course` | Recherche dans le catalogue des cours. |
| `GET /search/all` | Recherche globale dans les index. |

Les paramètres et les formats de réponse sont disponibles dans Swagger :
http://localhost:8000/docs.

## Metabase

Metabase démarre lorsque HiveServer2 et le metastore Hive sont disponibles.
Ouvrez http://localhost:3000, puis ajoutez Hive comme source de données afin
d'explorer les tables curées. Les requêtes utiles se trouvent dans
`dashboard/dashboard_queries.sql`.

## Tests et diagnostic

Tests unitaires Python :

```powershell
python -m pytest tests/ -v
```

Journaux des services principaux :

```powershell
docker logs --tail 80 university-airflow-webserver
docker logs --tail 80 university-airflow-scheduler
docker logs --tail 80 university-airflow-worker
docker logs --tail 80 university-minio
docker logs --tail 80 spark-master
docker logs --tail 80 spark-worker
```

Commandes de relance ciblée :

```powershell
docker compose up -d minio
docker compose up -d spark-master spark-worker
docker compose up -d airflow-webserver airflow-scheduler airflow-worker
```

Si l'interface Airflow ne répond pas après une première installation,
initialisez d'abord la base de métadonnées puis démarrez les composants Airflow :

```powershell
docker compose up airflow-init
docker compose up -d airflow-webserver airflow-scheduler airflow-worker
```

## État actuel et suite du projet

La plateforme dispose d'une chaîne complète allant de l'ingestion brute à la
recherche et à la visualisation : Airflow, MinIO, Spark, Hudi, Hive,
Elasticsearch, FastAPI et Metabase sont intégrés dans Docker Compose.

Le DAG `daily_ingestion` utilise désormais une stratégie d'exécution hybride
parallèle, permettant l'exécution simultanée des tâches indépendantes
d'ingestion, de transformation et d'indexation, tout en respectant les
dépendances entre les différentes étapes du pipeline.

Les améliorations possibles concernent notamment l'ajout de règles de qualité
de données, la surveillance des pipelines, l'authentification des interfaces
et le déploiement dans un environnement autre que local.

## Arrêt de l'infrastructure

```powershell
docker compose down
```

Cette commande conserve les volumes. La suppression des volumes efface les
données locales ; ne l'utilisez que si vous souhaitez réinitialiser la stack :

```powershell
docker compose down -v
```
