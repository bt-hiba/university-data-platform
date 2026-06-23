from pyspark.sql.functions import col


def remove_duplicates(df):
    return df.dropDuplicates()


def remove_null_faculty(df):

    return df.filter(
        col("faculty_id").isNotNull()
    )


def remove_null_courses(df):

    return df.filter(
        col("course_name").isNotNull()
    )


def validate_faculty_schema(df):

    required_columns = [
        "faculty_id",
        "faculty_name",
        "institution_name",
        "source_system"
    ]

    for column in required_columns:

        if column not in df.columns:
            raise Exception(
                f"Missing column {column}"
            )

    return True


def validate_course_schema(df):

    required_columns = [
        "course_id",
        "course_name"
    ]

    for column in required_columns:

        if column not in df.columns:
            raise Exception(
                f"Missing column {column}"
            )

    return True