from pyspark.sql import SparkSession

def get_hive_session():

    spark = (
        SparkSession.builder
        .appName("HiveClient")
        .enableHiveSupport()
        .getOrCreate()
    )

    return spark