from search.readers import read_faculty_profiles
from search.bulk_indexer import BulkIndexer
from search.config import FACULTY_INDEX


df = read_faculty_profiles()

indexer = BulkIndexer()

indexer.bulk_index_dataframe(
    dataframe=df,
    index_name=FACULTY_INDEX,
    id_field="faculty_id"
)