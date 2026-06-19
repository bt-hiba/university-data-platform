import os

try:
    from spark.spark_session import create_spark_session
except ModuleNotFoundError:
    from spark_session import create_spark_session


def main():
    raw_bucket = os.getenv("RAW_BUCKET", "raw-json")
    input_path = os.getenv("READ_MINIO_PATH", f"s3a://{raw_bucket}/")
    input_format = os.getenv("READ_MINIO_FORMAT", "text").lower()

    spark = create_spark_session()

    print(f"Reading MinIO path: {input_path}")
    print(f"Format: {input_format}")

    reader = spark.read.option("recursiveFileLookup", "true")

    if input_format == "json":
        df = reader.option("multiLine", "true").json(input_path)
    else:
        df = reader.text(input_path)

    print("Schema:")
    df.printSchema()

    print("Rows:", df.count())
    df.show(10, truncate=False)

    spark.stop()


if __name__ == "__main__":
    main()
