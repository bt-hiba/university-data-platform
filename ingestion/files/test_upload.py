from storage.minio_client import upload_file
from storage.minio_client import client

# fichier test local
file_path = "test.txt"

# créer un fichier test si pas existant
with open(file_path, "w", encoding="utf-8") as f:
    f.write("Hello MinIO - Test Upload ✔")

# choisir un bucket
bucket_name = "raw-json"

# nom dans MinIO
object_name = "test_upload.txt"

# upload
upload_file(bucket_name, object_name, file_path)

print("Test upload terminé ✔")