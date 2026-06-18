try:
    from spark.spark_session import create_spark_session
except ModuleNotFoundError:
    from spark_session import create_spark_session

spark = create_spark_session()

print("Spark Version:")
print(spark.version)

data = [
    ("Ahmed", "CS"),
    ("Fatima", "Math")
]

df = spark.createDataFrame(
    data,
    ["name", "department"]
)

print("Rows:", df.count())

df.show()

spark.stop()
