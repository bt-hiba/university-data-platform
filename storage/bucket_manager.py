from storage.minio_client import client

buckets = [
    "raw-web-html",
    "raw-documents",
    "raw-json",
    "raw-logs"
]

for bucket in buckets:

    if not client.bucket_exists(bucket):

        client.make_bucket(bucket)

        print(f"Bucket {bucket} created")

    else:
        print(f"Bucket {bucket} already exists")