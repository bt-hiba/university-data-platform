import sys
sys.path.insert(0, '/opt/spark-apps')
from spark_session import create_spark_session

spark = create_spark_session('Test')

print("="*60)
print("TEST spark_session.py")
print("="*60)

print("hive.metastore.uris =", spark.sparkContext.getConf().get('hive.metastore.uris'))
print("spark.sql.warehouse.dir =", spark.sparkContext.getConf().get('spark.sql.warehouse.dir'))
print("spark.hadoop.fs.s3a.endpoint =", spark.sparkContext.getConf().get('spark.hadoop.fs.s3a.endpoint'))

print("\nTables Hive:")
spark.sql("SHOW TABLES").show(truncate=False)

print("\nTest S3A:")
try:
    df = spark.read.format("hudi").load("s3a://curated/faculty_profiles")
    print("✓ faculty_profiles:", df.count(), "lignes")
except Exception as e:
    print("✗ faculty_profiles:", str(e)[:100])