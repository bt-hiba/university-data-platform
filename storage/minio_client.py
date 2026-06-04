from minio import Minio
from minio.error import S3Error
from dotenv import load_dotenv
import os

load_dotenv()

client = Minio(
    endpoint=os.getenv("MINIO_ENDPOINT"),
    access_key=os.getenv("MINIO_ACCESS_KEY"),
    secret_key=os.getenv("MINIO_SECRET_KEY"),
    secure=False
)

def upload_file(bucket_name, object_name, file_path):

    try:
        client.fput_object(
            bucket_name,
            object_name,
            file_path
        )

        print(f"Uploaded {object_name} to {bucket_name}")

    except S3Error as e:
        print("Error:", e)