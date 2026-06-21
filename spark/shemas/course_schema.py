from pyspark.sql.types import *

course_schema = StructType([

    StructField(
        "course_id",
        StringType(),
        False
    ),

    StructField(
        "course_name",
        StringType(),
        True
    ),

    StructField(
        "faculty",
        StringType(),
        True
    ),

    StructField(
        "program",
        StringType(),
        True
    ),

    StructField(
        "credits",
        IntegerType(),
        True
    ),

    StructField(
        "language",
        StringType(),
        True
    ),

    StructField(
        "source_system",
        StringType(),
        True
    )
])