from search.readers import read_course_catalog
from search.bulk_indexer import BulkIndexer
from search.config import COURSE_INDEX


df = read_course_catalog()

indexer = BulkIndexer()

indexer.bulk_index_dataframe(
    dataframe=df,
    index_name=COURSE_INDEX,
    id_field="course_id"
)