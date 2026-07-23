import os

ELASTIC_HOST = os.getenv("ELASTIC_HOST", "elasticsearch")
ELASTIC_PORT = int(os.getenv("ELASTIC_PORT", 9200))
ELASTIC_SCHEME = os.getenv("ELASTIC_SCHEME", "http")

FACULTY_INDEX = "faculty_profiles"
COURSE_INDEX = "course_catalog"