def normalize_course(row):

    return {
        "course_id": row.course_id,
        "course_name": row.course_name,
        "faculty": row.faculty,
        "program": row.program,
        "credits": row.credits,
        "language": row.language,
        "source_system": "csv"
    }