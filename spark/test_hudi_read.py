from spark_session import create_spark_session

spark = create_spark_session("hudi_read_test")

course_path = "s3a://curated/course_catalog"
faculty_path = "s3a://curated/faculty_profiles"

print("=== COURSE CATALOG ===")
df1 = spark.read.format("hudi").load(course_path)
df1.show()
print("Count:", df1.count())

print("=== FACULTY PROFILES ===")
df2 = spark.read.format("hudi").load(faculty_path)
df2.show()
print("Count:", df2.count())

spark.stop()