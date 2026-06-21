from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, lit, current_timestamp , explode_outer
from pyspark.sql.types import StructType, StructField, StringType, ArrayType, LongType
import os

# ----------------------------
# 1. Spark Session (IMPORTANT FIX MINIO)
# ----------------------------
spark = SparkSession.builder \
    .appName("UniversityDataPlatform") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.aws.credentials.provider",
            "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")


# ----------------------------
# 2. PATHS (TON MINIO STRUCTURE)
# ----------------------------
OPENALEX_PATH = "s3a://raw-json/source=openalex/year=2026/month=06/day=20/"
FACULTIES_PATH = "s3a://raw-json/source=local_files/year=2026/month=06/day=20/faculties.json"


# ----------------------------
# 3. FACULTIES (SAFE JSON READ)
# ----------------------------
faculties_df = spark.read.option("multiline", "true").json(FACULTIES_PATH)

print("=== FACULTIES ===")
faculties_df.printSchema()
faculties_df.show(truncate=False)


# ----------------------------
# 4. OPENALEX (ROBUST READ)
# ----------------------------

# 🔥 IMPORTANT FIX:
# on force lecture "text" puis parsing JSON propre
openalex_raw = spark.read.text(OPENALEX_PATH)

print("RAW COUNT =", openalex_raw.count())


# ----------------------------
# 5. JSON PARSING SAFE
# ----------------------------
from pyspark.sql.functions import from_json

schema = StructType([
    StructField("id", StringType(), True),
    StructField("title", StringType(), True),
    StructField("publication_year", LongType(), True),
    StructField("language", StringType(), True),

    StructField("authorships", ArrayType(
        StructType([
            StructField("institutions", ArrayType(
                StructType([
                    StructField("display_name", StringType(), True)
                ])
            ), True)
        ])
    ), True)
])

openalex_df = openalex_raw.select(
    from_json(col("value"), schema).alias("data")
).select("data.*")

print("=== OPENALEX SCHEMA ===")
openalex_df.printSchema()


# ----------------------------
# 6. TRANSFORM
# ----------------------------
works_df = openalex_df.select(
    col("id").alias("publication_id"),
    col("title").alias("publication_title"),
    col("publication_year"),
    col("language"),
    col("authorships")
)

# ----------------------------
# 7. EXPLODE AUTHORS + INSTITUTIONS (CORRECT)
# ----------------------------
from pyspark.sql.functions import explode_outer, col

authors_df = works_df \
    .withColumn("author", explode_outer("authorships")) \
    .withColumn("institution", explode_outer("author.institutions")) \
    .select(
        col("publication_id"),
        col("publication_title"),
        col("publication_year"),
        col("language"),
        col("institution.display_name").alias("institution_name")
    )
# ----------------------------
# 8. CLEAN NULLS (IMPORTANT)
# ----------------------------
authors_df = authors_df.filter(col("institution_name").isNotNull())
#bonus debug
authors_df.show(10, truncate=False)
authors_df.printSchema()
from pyspark.sql.functions import levenshtein, col, lit

# ----------------------------
# 9. FUZZY MATCHING (LEVENSHTEIN)
# ----------------------------

fuzzy_df = authors_df.crossJoin(faculties_df) \
    .withColumn(
        "distance",
        levenshtein(
            col("institution_name"),
            col("faculty_name")
        )
    ) \
    .filter(col("distance") <= 10)  # tu peux ajuster 5, 8, 12

# garder le meilleur match (le plus proche)
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number, asc

window = Window.partitionBy("publication_id", "institution_name").orderBy(asc("distance"))

final_df = fuzzy_df.withColumn("rn", row_number().over(window)) \
    .filter(col("rn") == 1)
# ----------------------------
# 10. FINAL OUTPUT
# ----------------------------
final_df = final_df.select(
    "faculty_name",
    lit("OpenAlex").alias("source_system"),
    "publication_title",
    "publication_year",
    "language",
    "faculty_id",
    "institution_name",
    "distance",
    current_timestamp().alias("ingestion_timestamp")
)

print("=== FINAL RESULT ===")
final_df.show(20, truncate=False)

