"""
DAG quotidien d'ingestion vers le Raw Zone (MinIO).

Pipeline :
    start → ensure_buckets → crawl_website → collect_api → collect_files
          → save_metadata → transform_faculty → transform_courses
          → register_hudi → index_faculty → index_courses → finish

Toutes les tâches partagent le même Python path (`/opt/airflow/project`)
monté depuis l'hôte par docker-compose, afin de pouvoir importer
les modules `ingestion/`, `storage/`, `utils/`, `configs/`.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

# Garantir l'import des modules du projet quel que soit l'exécuteur
PROJECT_ROOT = "/opt/airflow/project"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Logs d'ingestion isolés à côté des logs Airflow natifs
os.environ.setdefault("INGESTION_LOG_DIR", "/opt/airflow/logs/ingestion")


def _ensure_buckets(**_) -> list:
    from storage.bucket_manager import ensure_buckets
    return ensure_buckets()


def _crawl_website(**_) -> dict:
    from ingestion.web.crawler import run_crawler_from_env
    result = run_crawler_from_env()
    if result.pages_crawled == 0:
        raise RuntimeError(
            "Web crawler finished without uploading any HTML page "
            f"(failures={result.failures}). Check crawl_website logs."
        )
    return {
        "pages_crawled":        result.pages_crawled,
        "documents_downloaded": result.documents_downloaded,
        "failures":             result.failures,
    }


def _collect_api(**_) -> dict:
    from ingestion.api.api_ingestor import run_api_ingestion
    return run_api_ingestion()


def _collect_files(**_) -> list:
    from ingestion.files.file_loader import run_file_ingestion
    return run_file_ingestion()


def _save_metadata(**context) -> dict:
    """Récapitule les sorties de toutes les tâches d'ingestion dans raw-logs."""
    from storage.minio_client import upload_json
    from utils.time_utils import build_minio_date_path, get_timestamp_str

    ti = context["ti"]
    summary = {
        "run_id":         context["run_id"],
        "logical_date":   context["logical_date"].isoformat(),
        "completed_at":   get_timestamp_str(),
        "crawler":        ti.xcom_pull(task_ids="crawl_website"),
        "api":            ti.xcom_pull(task_ids="collect_api"),
        "files":          ti.xcom_pull(task_ids="collect_files"),
    }
    date_path = build_minio_date_path("pipeline")
    object_path = f"{date_path}/run_summary_{context['run_id']}.json"
    upload_json("raw-logs", object_path, summary)
    return summary


default_args = {
    "owner": "university-data-platform",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

SPARK_SUBMIT = """
set -euo pipefail
spark-submit \\
  --master "${{SPARK_MASTER}}" \\
  --conf spark.driver.host=airflow-worker \\
  --conf spark.driver.bindAddress=0.0.0.0 \\
  --conf spark.executor.cores=1 \\
  --conf spark.executor.memory=1g \\
  --conf spark.cores.max=2 \\
  {application}
""".strip()

SPARK_TASK_ENV = {
    # L'ingestion partitionne avec la date UTC d'exécution, pas la logical date
    # Airflow qui peut représenter le début de l'intervalle planifié.
    "PIPELINE_RUN_DATE": "{{ macros.datetime.utcnow().strftime('%Y-%m-%d') }}",
    "MINIO_ENDPOINT": "http://minio:9000",
}


with DAG(
    dag_id="daily_ingestion",
    description="Ingestion quotidienne (web + API + fichiers) vers MinIO Raw Zone",
    default_args=default_args,
    start_date=datetime(2026, 6, 1),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    tags=["raw-zone", "ingestion", "week-1"],
) as dag:

    start = EmptyOperator(task_id="start")

    ensure_buckets_task = PythonOperator(
        task_id="ensure_buckets",
        python_callable=_ensure_buckets,
    )

    crawl_website_task = PythonOperator(
        task_id="crawl_website",
        python_callable=_crawl_website,
    )

    collect_api_task = PythonOperator(
        task_id="collect_api",
        python_callable=_collect_api,
    )

    collect_files_task = PythonOperator(
        task_id="collect_files",
        python_callable=_collect_files,
    )

    save_metadata_task = PythonOperator(
        task_id="save_metadata",
        python_callable=_save_metadata,
    )

    transform_faculty_task = BashOperator(
        task_id="transform_faculty_profiles",
        bash_command=SPARK_SUBMIT.format(
            application="/opt/airflow/project/spark/transform_faculty_profiles.py"
        ),
        env=SPARK_TASK_ENV,
        append_env=True,
    )

    transform_courses_task = BashOperator(
        task_id="transform_course_catalog",
        bash_command=SPARK_SUBMIT.format(
            application="/opt/airflow/project/spark/transform_course_catalog.py"
        ),
        env=SPARK_TASK_ENV,
        append_env=True,
    )

    register_hudi_task = BashOperator(
        task_id="register_hudi_tables",
        bash_command=SPARK_SUBMIT.format(
            application="/opt/airflow/project/hive/register_hudi_tables.py"
        ),
        env=SPARK_TASK_ENV,
        append_env=True,
    )

    index_faculty_task = BashOperator(
        task_id="index_faculty",
        bash_command=SPARK_SUBMIT.format(
            application="/opt/airflow/project/search/index_faculty.py"
        ),
        env=SPARK_TASK_ENV,
        append_env=True,
    )

    index_courses_task = BashOperator(
        task_id="index_courses",
        bash_command=SPARK_SUBMIT.format(
            application="/opt/airflow/project/search/index_courses.py"
        ),
        env=SPARK_TASK_ENV,
        append_env=True,
    )

    finish = EmptyOperator(task_id="finish")

    (
        start
        >> ensure_buckets_task
        >> crawl_website_task
        >> collect_api_task
        >> collect_files_task
        >> save_metadata_task
        >> transform_faculty_task
        >> transform_courses_task
        >> register_hudi_task
        >> index_faculty_task
        >> index_courses_task
        >> finish
    )
