from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, current_timestamp, levenshtein, row_number,
    lower, trim, regexp_replace, length, broadcast 
)
from pyspark.sql.types import StructType, StructField, StringType, LongType 
from pyspark.sql.window import Window
from pyspark.sql.functions import asc
import json 

from quality_checks import (
    remove_duplicates,
    remove_null_faculty,
    validate_faculty_schema
)



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

OPENALEX_PATH = "s3a://raw-json/source=openalex/year=2026/month=06/day=20/openalex_publications_20260620T120138Z_be959a0a5742.json"
FACULTIES_PATH = "s3a://raw-json/source=local_files/year=2026/month=06/day=20/faculties.json"

# ----------------------------
# READ FACULTIES
# ----------------------------
print("\n=== LOADING FACULTIES ===")
faculties_df = spark.read.option("multiline", "true").json(FACULTIES_PATH)
print(f"✓ Faculties: {faculties_df.count()} rows")
faculties_df.show()

# Normalize faculty names
faculties_df = faculties_df.withColumn(
    "faculty_clean",
    lower(trim(regexp_replace(col("faculty_name"), "[^a-zA-Z0-9 ]", "")))
)


# ----------------------------
# READ & PARSE OPENALEX (text -> Python JSON)
# ----------------------------
print("\n=== LOADING OPENALEX ===")

raw = spark.read.text(OPENALEX_PATH).collect()
all_text = "".join([row.value for row in raw])
publications = json.loads(all_text)

print(f"Total publications: {len(publications)}")

# Extract authors with institutions
authors_data = []
for pub in publications:
    pub_id = pub.get("id", "")
    pub_title = pub.get("title", "")
    pub_year = pub.get("publication_year")
    pub_lang = pub.get("language", "")

    authorships = pub.get("authorships", [])

    for authorship in authorships:
        institutions = authorship.get("institutions", [])

        for inst in institutions:
            inst_name = inst.get("display_name", "")

            if inst_name:  # Only keep non-empty institution names
                authors_data.append({
                    "publication_id": pub_id,
                    "publication_title": pub_title,
                    "publication_year": pub_year,
                    "language": pub_lang,
                    "institution_name": inst_name
                })

print(f"Author-institution pairs: {len(authors_data)}")

# Create DataFrame from Python data
if len(authors_data) > 0:
    authors_df = spark.createDataFrame(authors_data)
    authors_df.show(5)

    # Normalize institution names
    authors_df = authors_df.withColumn(
        "institution_clean",
        lower(trim(regexp_replace(col("institution_name"), "[^a-zA-Z0-9 ]", "")))
    )
else:
    print("⚠ No author-institution pairs found!")
    authors_df = None


# ----------------------------
# FUZZY MATCH WITH FACULTIES
# ----------------------------
if authors_df is not None and authors_df.count() > 0:
    print("\n=== FUZZY MATCHING (with broadcast optimization) ===")

    # Use broadcast to optimize crossJoin
    fuzzy_df = authors_df.crossJoin(broadcast(faculties_df)) \
        .withColumn(
            "distance",
            levenshtein(
                col("institution_clean"),
                col("faculty_clean")
            )
        ) \
        .withColumn(
            "score",
            (1 / (col("distance") + 1)) + (1 / (length(col("faculty_clean")) + 1))
        ) \
        .filter(col("score") > 0.2)

    print(f"Matches (score > 0.2): {fuzzy_df.count()}")

    if fuzzy_df.count() > 0:
        window = Window.partitionBy("publication_id", "institution_name").orderBy(asc("distance"))
        final_df = fuzzy_df.withColumn("rn", row_number().over(window)) \
            .filter(col("rn") == 1) \
            .drop("rn")

        final_df = final_df.select(
            "faculty_name",
            lit("OpenAlex").alias("source_system"),
            "publication_title",
            "publication_year",
            "language",
            "faculty_id",
            "institution_name",
            "distance",
            "score",
            current_timestamp().alias("ingestion_timestamp")
        )

        print("\n=== FINAL RESULT ===")
        print(f"Final: {final_df.count()} records")
        final_df.show(truncate=False)
        print("===== BEFORE QUALITY =====")
        print(final_df.count())

        final_df = remove_duplicates(final_df)

        final_df = remove_null_faculty(final_df)

        validate_faculty_schema(final_df)

        print("===== AFTER QUALITY =====")
        print(final_df.count())
    else:
        print("No fuzzy matches found!")
else:
    print("Could not process data")

