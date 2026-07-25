from typing import Generator
from typing import Dict
from typing import Any

import logging
import time

from elasticsearch import helpers
from elasticsearch.helpers import BulkIndexError

from search.elastic_client import get_client


logger = logging.getLogger(__name__)

client = get_client()


class BulkIndexer:
    """
    Generic Spark -> Elasticsearch Bulk Indexer.

    Responsibilities
    ----------------
    - Convert Spark DataFrame into Elasticsearch documents.
    - Send documents using Elasticsearch Bulk API.
    - Retry on failure.
    - Produce execution statistics.
    """

    def __init__(
        self,
        chunk_size: int = 500,
        max_retries: int = 3,
        retry_delay: int = 5,
        refresh: bool = True,
    ):

        self.chunk_size = chunk_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.refresh = refresh

    ####################################################################

    def dataframe_to_actions(
        self,
        dataframe,
        index_name: str,
        id_field: str,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Convert Spark DataFrame into Bulk API actions.
        """
        for row in dataframe.toLocalIterator():
            document = row.asDict(recursive=True)

            # DEBUG
            print("DOCUMENT:")
            print(document)

            yield {
                "_index": index_name,
                "_id": str(document[id_field]),
                "_source": document,
            }


    ####################################################################

    def bulk_index_dataframe(
        self,
        dataframe,
        index_name: str,
        id_field: str,
    ) -> None:

        logger.info("=" * 60)
        logger.info("Starting Bulk Indexing")
        logger.info(f"Index : {index_name}")

        actions = self.dataframe_to_actions(
            dataframe=dataframe,
            index_name=index_name,
            id_field=id_field,
        )

        attempt = 1

        while attempt <= self.max_retries:

            try:

                success, failed = helpers.bulk(

                    client,

                    actions,

                    chunk_size=self.chunk_size,

                    raise_on_error=True,

                    stats_only=True,

                    refresh=self.refresh,

                )

                logger.info(f"Indexed documents : {success}")

                logger.info(f"Failed documents  : {failed}")

                logger.info("Bulk indexing completed successfully.")

                return

            except BulkIndexError as error:

                logger.error(
                    f"BulkIndexError (Attempt {attempt}/{self.max_retries})"
                )

                logger.error(error)

                if attempt == self.max_retries:

                    logger.error("Maximum retry reached.")

                    raise

                logger.info(
                    f"Retry in {self.retry_delay} seconds..."
                )

                time.sleep(self.retry_delay)

                attempt += 1

        logger.info("=" * 60)
