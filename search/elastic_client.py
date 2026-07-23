from elasticsearch import Elasticsearch


def get_client():

    return Elasticsearch(
        "http://elasticsearch:9200"
    )