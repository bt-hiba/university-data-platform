from search.config import FACULTY_INDEX, COURSE_INDEX


FACULTY_MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "properties": {

            "faculty_id": {
                "type": "long"
            },

            "faculty_name": {
                "type": "text"
            },

            "institution_name": {
                "type": "text"
            },

            "publication_title": {
                "type": "text"
            },

            "publication_year": {
                "type": "integer"
            },

            "language": {
                "type": "keyword"
            },

            "source_system": {
                "type": "keyword"
            },

            "distance": {
                "type": "integer"
            },

            "score": {
                "type": "float"
            },

            "ingestion_timestamp": {
                "type": "date"
            }

        }
    }
}


COURSE_MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "properties": {

            "course_id": {
                "type": "keyword"
            },

            "course_name": {
                "type": "text"
            },

            "faculty": {
                "type": "text"
            },

            "course_code": {
                "type": "keyword"
            },

            "faculty_normalized": {
                "type": "keyword"
            },

            "source_system": {
                "type": "keyword"
            },

            "ingestion_timestamp": {
                "type": "date"
            }

        }
    }
}