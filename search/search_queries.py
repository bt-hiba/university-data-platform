"""
search_queries.py

Fonctions de recherche Elasticsearch pour le University Data Platform.

Ce module fournit les recherches sur les index :
- faculty_profiles
- course_catalog
"""

from search.elastic_client import get_client
from search.config import FACULTY_INDEX
from search.config import COURSE_INDEX
from search.utils import format_hits


# Connexion Elasticsearch
client = get_client()


# ==========================================================
# Faculty Search
# ==========================================================

def search_faculty(keyword: str, size: int = 10):
    """
    Recherche dans les profils des enseignants.

    Recherche sur :
    - faculty_name
    - publication_title
    - institution_name
    """

    response = client.search(
        index=FACULTY_INDEX,
        body={
            "size": size,
            "query": {
                "multi_match": {
                    "query": keyword,
                    "fields": [
                        "faculty_name",
                        "publication_title",
                        "institution_name"
                    ]
                }
            }
        }
    )

    return format_hits(response)


# ==========================================================
# Course Search
# ==========================================================

def search_courses(keyword: str, size: int = 10):
    """
    Recherche dans le catalogue des cours.

    Recherche sur :
    - course_name
    - course_code
    - faculty
    """

    response = client.search(
        index=COURSE_INDEX,
        body={
            "size": size,
            "query": {
                "multi_match": {
                    "query": keyword,
                    "fields": [
                        "course_name",
                        "course_code",
                        "faculty"
                    ]
                }
            }
        }
    )

    return format_hits(response)


# ==========================================================
# Search by Language
# ==========================================================

def search_by_language(language: str, size: int = 20):
    """
    Recherche des publications selon leur langue.
    """

    response = client.search(
        index=FACULTY_INDEX,
        body={
            "size": size,
            "query": {
                "term": {
                    "language.keyword": language
                }
            }
        }
    )

    return format_hits(response)


# ==========================================================
# Search by Publication Year
# ==========================================================

def search_by_year(year: int, size: int = 20):
    """
    Recherche des publications selon l'année.
    """

    response = client.search(
        index=FACULTY_INDEX,
        body={
            "size": size,
            "query": {
                "term": {
                    "publication_year": year
                }
            }
        }
    )

    return format_hits(response)


# ==========================================================
# Global Search
# ==========================================================

def search_everything(keyword: str, size: int = 10):
    """
    Recherche dans tous les index disponibles.
    """

    return {

        "faculty_profiles": search_faculty(
            keyword=keyword,
            size=size
        ),

        "course_catalog": search_courses(
            keyword=keyword,
            size=size
        )

    }


# ==========================================================
# Main (Tests)
# ==========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("Faculty Search")
    print("=" * 60)

    faculty_results = search_faculty("machine")

    print(faculty_results)

    print()

    print("=" * 60)
    print("Course Search")
    print("=" * 60)

    course_results = search_courses("python")

    print(course_results)

    print()

    print("=" * 60)
    print("Search by Language")
    print("=" * 60)

    language_results = search_by_language("en")

    print(language_results)

    print()

    print("=" * 60)
    print("Search by Year")
    print("=" * 60)

    year_results = search_by_year(2024)

    print(year_results)

    print()

    print("=" * 60)
    print("Global Search")
    print("=" * 60)

    all_results = search_everything("machine")

    print(all_results)