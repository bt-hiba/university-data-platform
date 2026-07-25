from search.elastic_client import get_client
from search.config import FACULTY_INDEX, COURSE_INDEX
from search.mappings import FACULTY_MAPPING, COURSE_MAPPING


client = get_client()


def create_index(index_name, mapping):

    if client.indices.exists(index=index_name):

        print(f"{index_name} already exists.")

        return

    client.indices.create(
        index=index_name,
        body=mapping
    )

    print(f"{index_name} created.")


def main():

    create_index(
        FACULTY_INDEX,
        FACULTY_MAPPING
    )

    create_index(
        COURSE_INDEX,
        COURSE_MAPPING
    )


if __name__ == "__main__":

    main()