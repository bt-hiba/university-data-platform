import uuid

from spark.utils.regex_utils import (
    extract_email,
    extract_department
)

def build_faculty_profile(text):

    return {
        "faculty_id": str(uuid.uuid4()),
        "name": None,
        "department": extract_department(text),
        "email": extract_email(text)
    }