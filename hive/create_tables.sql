--Pour faculty_profiles--

CREATE TABLE IF NOT EXISTS faculty_profiles
USING HUDI
LOCATION 's3a://curated/faculty_profiles';

--Pour course_catalog--

CREATE TABLE IF NOT EXISTS course_catalog
USING HUDI
LOCATION 's3a://curated/course_catalog';
