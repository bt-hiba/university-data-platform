#!/usr/bin/env python3
"""
Script pour créer et enregistrer les tables Hudi dans le metastore Hive
"""

from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType
from datetime import datetime, timedelta
import sys

def get_hive_spark_session():
    """Crée une session Spark avec support Hive et Hudi"""
    spark = (
        SparkSession.builder
        .appName("HudiRegistration")
        .config("spark.sql.warehouse.dir", "/user/hive/warehouse")
        .config("spark.hadoop.fs.s3a.endpoint", "http://university-minio:9000")
        .config("spark.hadoop.fs.s3a.access.key", "minioadmin")
        .config("spark.hadoop.fs.s3a.secret.key", "minioadmin")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("hive.metastore.uris", "thrift://hive-metastore:9083")
        .config("spark.sql.catalogImplementation", "hive")
        .enableHiveSupport()
        .getOrCreate()
    )
    return spark

def write_hudi_table(spark, table_name, record_key, path, data):
    """Écrit des données avec Hudi et les enregistre dans Hive"""

    # Écrire avec Hudi
    hudi_options = {
        "hoodie.table.name": table_name,
        "hoodie.datasource.write.recordkey.field": record_key,
        "hoodie.datasource.write.precombine.field": "ingestion_timestamp",
        "hoodie.datasource.write.operation": "upsert",
        "hoodie.datasource.write.table.type": "COPY_ON_WRITE"
    }

    print(f"[INFO] Écriture des données Hudi pour {table_name}...")
    data.write.format("hudi") \
        .options(**hudi_options) \
        .mode("overwrite") \
        .save(path)

    print(f"[INFO] Données écrites à: {path}")

    # Enregistrer dans Hive
    print(f"[INFO] Enregistrement de la table {table_name} dans Hive...")
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {table_name}
        USING HUDI
        LOCATION '{path}'
    """)

    print(f"[✓] Table {table_name} enregistrée avec succès")

def create_faculty_data():
    """Génère des données d'exemple pour faculty_profiles"""
    spark = SparkSession.builder.getOrCreate()

    data = [
        ("PROF001", "Jean Dupont", "jean@university.edu", "Informatique", datetime.now()),
        ("PROF002", "Marie Martin", "marie@university.edu", "Mathématiques", datetime.now()),
        ("PROF003", "Pierre Bernard", "pierre@university.edu", "Physique", datetime.now()),
        ("PROF004", "Sophie Leclerc", "sophie@university.edu", "Chimie", datetime.now()),
    ]

    schema = StructType([
        StructField("faculty_id", StringType(), True),
        StructField("name", StringType(), True),
        StructField("email", StringType(), True),
        StructField("department", StringType(), True),
        StructField("ingestion_timestamp", TimestampType(), True),
    ])

    return spark.createDataFrame(data, schema=schema)

def create_course_data():
    """Génère des données d'exemple pour course_catalog"""
    spark = SparkSession.builder.getOrCreate()

    data = [
        ("CS101", "Introduction à l'Informatique", "PROF001", 30, datetime.now()),
        ("CS201", "Programmation Avancée", "PROF001", 25, datetime.now()),
        ("MATH101", "Calcul I", "PROF002", 50, datetime.now()),
        ("MATH201", "Calcul II", "PROF002", 40, datetime.now()),
        ("PHYS101", "Mécanique", "PROF003", 35, datetime.now()),
        ("CHEM101", "Chimie Générale", "PROF004", 45, datetime.now()),
    ]

    schema = StructType([
        StructField("course_id", StringType(), True),
        StructField("course_name", StringType(), True),
        StructField("instructor_id", StringType(), True),
        StructField("max_students", IntegerType(), True),
        StructField("ingestion_timestamp", TimestampType(), True),
    ])

    return spark.createDataFrame(data, schema=schema)

def main():
    print("[INFO] Démarrage du script d'enregistrement Hudi...")

    try:
        # Créer la session Spark
        spark = get_hive_spark_session()
        print("[✓] Session Spark créée")

        # Générer les données
        print("\n[INFO] Génération des données d'exemple...")
        faculty_df = create_faculty_data()
        course_df = create_course_data()
        print("[✓] Données générées")

        # Écrire les tables Hudi
        print("\n[INFO] Écriture des tables Hudi...")
        write_hudi_table(spark, "faculty_profiles", "faculty_id",
                        "s3a://curated/faculty_profiles", faculty_df)
        write_hudi_table(spark, "course_catalog", "course_id",
                        "s3a://curated/course_catalog", course_df)

        # Vérifier que les tables sont enregistrées
        print("\n[INFO] Vérification des tables enregistrées...")
        spark.sql("SHOW TABLES").show()

        print("\n[INFO] Vérification du contenu des tables...")
        spark.sql("SELECT * FROM faculty_profiles").show()
        spark.sql("SELECT * FROM course_catalog").show()

        print("\n[✓] Script d'enregistrement Hudi terminé avec succès!")

    except Exception as e:
        print(f"[✗] Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
