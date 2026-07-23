from search.elastic_client import get_client

client = get_client()

print(client.info())