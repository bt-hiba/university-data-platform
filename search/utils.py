from typing import List
from typing import Dict


def format_hits(response) -> List[Dict]:
    """
    Transforme la réponse Elasticsearch en liste JSON simple.
    """

    hits = response["hits"]["hits"]

    results = []

    for hit in hits:

        document = hit["_source"].copy()

        document["score"] = hit["_score"]

        results.append(document)

    return results