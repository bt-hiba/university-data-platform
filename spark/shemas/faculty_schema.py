from pyspark.sql.types import *

faculty_schema = StructType([

    StructField(
        "faculty_id",
        StringType(),
        False
    ),

    StructField(
        "name",
        StringType(),
        True
    ),

    StructField(
        "department",
        StringType(),
        True
    ),

    StructField(
        "email",
        StringType(),
        True
    ),

    StructField(
        "source_url",
        StringType(),
        True
    ),

    StructField(
        "source_system",
        StringType(),
        True
    ),

    StructField(
        "crawl_timestamp",
        StringType(),
        True
    ),

    StructField(
        "content_hash",
        StringType(),
        True
    )
])