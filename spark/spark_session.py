from pyspark.sql import SparkSession
import os

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()


def create_spark_session():
    spark_master = os.getenv("SPARK_MASTER", "spark://spark-master:7077")
    minio_endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    minio_access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    minio_secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")

    spark = (
        SparkSession.builder
        .appName("UniversityDataPlatform")
        .master(spark_master)

        .config(
            "spark.hadoop.fs.s3a.endpoint",
            minio_endpoint
        )

        .config(
            "spark.hadoop.fs.s3a.access.key",
            minio_access_key
        )

        .config(
            "spark.hadoop.fs.s3a.secret.key",
            minio_secret_key
        )

        .config(
            "spark.hadoop.fs.s3a.path.style.access",
            "true"
        )

        .config(
            "spark.hadoop.fs.s3a.connection.ssl.enabled",
            "false"
        )

        .getOrCreate()
    )

    return spark
