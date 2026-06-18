from spark.spark_session import create_spark_session

spark = create_spark_session()

print("Spark Version")

print(spark.version)

data = [
    ("Ahmed", "CS"),
    ("Fatima", "Math")
]

df = spark.createDataFrame(
    data,
    ["name", "department"]
)

df.show()