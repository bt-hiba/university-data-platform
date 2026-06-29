#!/usr/bin/env python3
"""
Registre les tables Hudi EXISTANTES dans Hive Metastore via Spark.
À exécuter APRÈS transform_faculty_profiles.py et transform_course_catalog.py
NE PAS exécuter create_hudi_tables.py avant (il écrase les données).
"""

import sys
sys.path.append('/opt/spark-apps')

from spark_session import create_spark_session

def main():
    print("=" * 60)
    print("REGISTRATION DES TABLES HUDI DANS HIVE")
    print("=" * 60)
    
    spark = create_spark_session("HudiRegistration")
    print("[✓] Session Spark créée")
    
    # Vérifier connexion Hive
    print("\n[INFO] Tables existantes:")
    try:
        spark.sql("SHOW TABLES").show(truncate=False)
    except Exception as e:
        print(f"  ⚠ {e}")
    
    tables = [
        ("faculty_profiles", "s3a://curated/faculty_profiles"),
        ("course_catalog", "s3a://curated/course_catalog"),
    ]
    
    for table_name, path in tables:
        print(f"\n[INFO] Registration {table_name}...")
        
        # Vérifier que les données existent
        try:
            df_check = spark.read.format("hudi").load(path)
            count = df_check.count()
            print(f"  ✓ Données Hudi trouvées: {count} lignes")
        except Exception as e:
            print(f"  ✗ ERREUR: Pas de données Hudi à {path}")
            print(f"    {e}")
            continue
        
        # DROP si existe (pour éviter conflits)
        print(f"  [INFO] DROP TABLE IF EXISTS {table_name}")
        spark.sql(f"DROP TABLE IF EXISTS {table_name}")
        
        # CREATE TABLE USING HUDI
        print(f"  [INFO] CREATE TABLE {table_name}")
        spark.sql(f"""
            CREATE TABLE {table_name}
            USING HUDI
            LOCATION '{path}'
        """)
        
        print(f"  ✓ Table {table_name} registrée!")
    
    # Vérification finale
    print("\n" + "=" * 60)
    print("VERIFICATION FINALE")
    print("=" * 60)
    
    print("\n[INFO] Tables Hive:")
    spark.sql("SHOW TABLES").show(truncate=False)
    
    for table_name, _ in tables:
        print(f"\n[INFO] SELECT COUNT(*) FROM {table_name}:")
        try:
            spark.sql(f"SELECT COUNT(*) FROM {table_name}").show()
        except Exception as e:
            print(f"  ✗ Erreur: {e}")
    
    print("\n[✓] Terminé!")

if __name__ == "__main__":
    main()