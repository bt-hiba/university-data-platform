# test_utils_integration.py
# Ce fichier simule comment les Membres 2, 3, 4 vont utiliser ton travail.
# Tu peux le supprimer une fois les tests passés.

print("=" * 60)
print("TEST D'INTÉGRATION — utils (Membre 5)")
print("=" * 60)

# ── Test 1 : time_utils ───────────────────────────────────────
print("\n📅 Test time_utils...")
from utils.time_utils import get_timestamp_str, get_date_parts, build_minio_date_path

ts = get_timestamp_str()
parts = get_date_parts()
path_api  = build_minio_date_path("openalex")
path_web  = build_minio_date_path("um5")
path_file = build_minio_date_path("csv")

assert isinstance(ts, str) and len(ts) > 10, "Timestamp invalide"
assert len(parts["month"]) == 2, "Le mois doit avoir 2 chiffres"
assert len(parts["day"]) == 2,   "Le jour doit avoir 2 chiffres"
assert path_api.startswith("source=openalex/"), "Chemin API invalide"
assert path_web.startswith("source=um5/"),      "Chemin web invalide"

print(f"  ✅ Timestamp      : {ts}")
print(f"  ✅ Date parts     : {parts}")
print(f"  ✅ Chemin API     : {path_api}")
print(f"  ✅ Chemin web     : {path_web}")
print(f"  ✅ Chemin fichier : {path_file}")

# ── Test 2 : hash_utils ───────────────────────────────────────
print("\n🔐 Test hash_utils...")
from utils.hash_utils import compute_hash_from_bytes, compute_hash_from_text, compute_hash_from_file

h_text1 = compute_hash_from_text("contenu de test")
h_text2 = compute_hash_from_text("contenu de test")
h_text3 = compute_hash_from_text("contenu différent")
h_bytes = compute_hash_from_bytes(b"hello world")

assert h_text1 == h_text2, "Le hash doit être déterministe"
assert h_text1 != h_text3, "Des contenus différents doivent avoir des hashs différents"
assert len(h_bytes) == 64,  "SHA-256 doit produire 64 caractères"

print(f"  ✅ Hash déterministe     : {h_text1 == h_text2}")
print(f"  ✅ Hash sensible aux diff: {h_text1 != h_text3}")
print(f"  ✅ Longueur SHA-256      : {len(h_bytes)} caractères")

# Test sur un vrai fichier (requirements.txt existe forcément)
h_file = compute_hash_from_file("requirements.txt")
assert len(h_file) == 64, "Hash de fichier invalide"
print(f"  ✅ Hash de fichier       : {h_file[:20]}...")

# ── Test 3 : logger ───────────────────────────────────────────
print("\n📋 Test logger...")
from utils.logger import (
    setup_logger, log_ingestion_start, log_ingestion_success,
    log_ingestion_error, log_retry, log_metadata
)
import os

log = setup_logger("integration_test")

log_ingestion_start(log, "openalex", "api")
log_ingestion_success(log, "openalex", "raw-json/source=openalex/data.json", h_bytes, 2048)
log_ingestion_error(log, "um5", ConnectionError("Timeout"), "GET https://um5.ac.ma")
log_retry(log, "um5", attempt=1, max_attempts=3, wait_seconds=2)
log_metadata(log, {
    "source": "openalex",
    "hash": h_bytes,
    "timestamp": ts,
    "path": path_api
})

# Vérifier que le fichier de log a été créé
parts = get_date_parts()
base_log_dir = os.getenv("INGESTION_LOG_DIR", "logs")
log_path = os.path.join(base_log_dir, parts["year"], parts["month"], parts["day"], "integration_test.log")
assert os.path.exists(log_path), f"Fichier de log non créé : {log_path}"
print(f"  ✅ Fichier de log créé : {log_path}")

# ── Résumé ────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("✅ TOUS LES TESTS PASSÉS — utils prêt pour intégration")
print("=" * 60)