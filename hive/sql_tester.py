from hive.hive_client import get_hive_session

spark = get_hive_session()

spark.sql(
    """
    SELECT *
    FROM faculty_profiles
    LIMIT 10
    """
).show()

spark.sql(
    """
    SELECT COUNT(*)
    FROM course_catalog
    """
).show()