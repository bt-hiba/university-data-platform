import re

EMAIL_PATTERN = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

DEPARTMENT_PATTERNS = [
    r"Department of ([A-Za-z ]+)",
    r"Département de ([A-Za-z ]+)",
    r"Département ([A-Za-z ]+)"
]


def extract_email(text):

    match = re.search(
        EMAIL_PATTERN,
        text
    )

    return match.group(0) if match else None


def extract_department(text):

    for pattern in DEPARTMENT_PATTERNS:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return match.group(1).strip()

    return None