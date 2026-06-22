import os
from pyspark.sql import SparkSession

def create_spark_session(app_name="UniversityDataPlatform"):

    spark_master = os.getenv("SPARK_MASTER", "spark://spark-master:7077")
    minio_endpoint = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
    access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")

    return SparkSession.builder \
        .appName(app_name) \
        .master(spark_master) \
        .config("spark.serializer",
                "org.apache.spark.serializer.KryoSerializer") \
        .config("spark.sql.extensions",
                "org.apache.spark.sql.hudi.HoodieSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog",
                "org.apache.spark.sql.hudi.catalog.HoodieCatalog") \
        .config("spark.hadoop.fs.s3a.endpoint", minio_endpoint) \
        .config("spark.hadoop.fs.s3a.access.key", access_key) \
        .config("spark.hadoop.fs.s3a.secret.key", secret_key) \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl",
                "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .getOrCreate()