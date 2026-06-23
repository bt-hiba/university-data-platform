from hive.hive_client import get_hive_session

spark = get_hive_session()

spark.sql("""
CREATE TABLE IF NOT EXISTS faculty_profiles
USING HUDI
LOCATION 's3a://curated/faculty_profiles'
""")

spark.sql("""
CREATE TABLE IF NOT EXISTS course_catalog
USING HUDI
LOCATION 's3a://curated/course_catalog'
""")

print("Tables registered successfully")