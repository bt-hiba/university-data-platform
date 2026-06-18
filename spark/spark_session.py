from pyspark.sql import SparkSession
from dotenv import load_dotenv
import os

load_dotenv()


def create_spark_session():

    spark = (
        SparkSession.builder
        .appName("UniversityDataPlatform")
        .master("spark://spark-master:7077")

        .config(
            "spark.hadoop.fs.s3a.endpoint",
            os.getenv("MINIO_ENDPOINT")
        )

        .config(
            "spark.hadoop.fs.s3a.access.key",
            os.getenv("MINIO_ACCESS_KEY")
        )

        .config(
            "spark.hadoop.fs.s3a.secret.key",
            os.getenv("MINIO_SECRET_KEY")
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