import sys
from pyspark.sql import functions as F

sys.path.append("/opt/spark-apps")

from spark_session import create_spark_session

from quality_checks import (
    remove_duplicates,
    remove_null_courses,
    validate_course_schema
)



if __name__ == "__main__":

    spark = create_spark_session("course_catalog_transform")
    
    

    # READ CSV FROM MINIO
    df = spark.read.option("header", True).csv(
    "s3a://raw-documents/source=local_files/year=2026/month=06/day=20/courses.csv"
    )

    # CLEAN
    df_clean = df.select(
        F.col("course_id").cast("int"),
        F.col("course_name"),
        F.col("faculty")
    )

    # TRANSFORM
    df_final = df_clean.withColumn(
        "course_code",
        F.concat(F.lit("COURSE_"), F.col("course_id"))
    ).withColumn(
        "faculty_normalized",
        F.upper(F.col("faculty"))
    ).withColumn(
        "source_system",
        F.lit("csv_ingestion")
    ).withColumn(
        "ingestion_timestamp",
        F.current_timestamp()
    )

    
    df_final.show(truncate=False)

    print("===== BEFORE QUALITY =====")
    print(df_final.count())

    df_final = remove_duplicates(df_final)

    df_final = remove_null_courses(df_final)

    validate_course_schema(df_final)

    print("===== AFTER QUALITY =====")
    print(df_final.count())
    # WRITE
    df_final.write.mode("overwrite").parquet(
        "s3a://curated/course_catalog/"
    )
    print("✓ Written to s3a://curated/course_catalog/")
    df.printSchema()
    df.show()
    spark.stop()
    