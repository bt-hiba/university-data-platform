from spark_session import create_spark_session

spark = create_spark_session("Elasticsearch Reader")


def read_faculty_profiles():

    return spark.sql("""

        SELECT

            faculty_id,
            faculty_name,
            institution_name,
            publication_title,
            publication_year,
            language,
            source_system,
            distance,
            score,
            ingestion_timestamp

        FROM faculty_profiles

    """)


def read_course_catalog():

    return spark.sql("""

        SELECT

            course_id,
            course_name,
            faculty,
            course_code,
            faculty_normalized,
            source_system,
            ingestion_timestamp

        FROM course_catalog

    """)