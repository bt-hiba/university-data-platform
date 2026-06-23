def write_hudi(df, table_name, record_key, path):

    hudi_options = {
        "hoodie.table.name": table_name,
        "hoodie.datasource.write.recordkey.field": record_key,
        "hoodie.datasource.write.precombine.field":
            "ingestion_timestamp",
        "hoodie.datasource.write.operation": "upsert",
        "hoodie.datasource.write.table.type":
            "COPY_ON_WRITE"
    }

    df.write.format("hudi") \
        .options(**hudi_options) \
        .mode("overwrite") \
        .save(path)