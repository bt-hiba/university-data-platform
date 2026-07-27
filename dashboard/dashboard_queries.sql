-- ============================================
-- QUESTION 1 : Total Faculty
-- ============================================
SELECT COUNT(*) AS total_faculty
FROM faculty_profiles;

-- ============================================
-- QUESTION 2 : Total Courses
-- ============================================
SELECT COUNT(*) AS total_courses
FROM course_catalog;

-- ============================================
-- QUESTION 3 : Courses by Faculty
-- ============================================
SELECT 
    COALESCE(faculty_normalized, faculty, 'Unknown') AS faculty_name,
    COUNT(*) AS total_courses
FROM course_catalog
WHERE faculty IS NOT NULL OR faculty_normalized IS NOT NULL
GROUP BY COALESCE(faculty_normalized, faculty, 'Unknown')
ORDER BY total_courses DESC;

-- ============================================
-- QUESTION 4 : Faculty Profiles by Source
-- ============================================
SELECT 
    COALESCE(source_system, 'Unknown') AS data_source,
    COUNT(*) AS profile_count
FROM faculty_profiles
GROUP BY source_system
ORDER BY profile_count DESC;

-- ============================================
-- QUESTION 5 : Publications by Year
-- ============================================
SELECT 
    COALESCE(CAST(publication_year AS STRING), 'Unknown') AS pub_year,
    COUNT(*) AS publication_count
FROM faculty_profiles
WHERE publication_year IS NOT NULL
GROUP BY publication_year
ORDER BY publication_year DESC;

-- ============================================
-- QUESTION 6 : Top 10 Institutions
-- ============================================
SELECT 
    COALESCE(institution_name, 'Unknown') AS institution,
    COUNT(*) AS publication_count
FROM faculty_profiles
WHERE institution_name IS NOT NULL
GROUP BY institution_name
ORDER BY publication_count DESC
LIMIT 10;

-- ============================================
-- QUESTION 7 : Ingestion Activity
-- ============================================
SELECT 
    DATE(ingestion_timestamp) AS ingestion_date,
    COUNT(*) AS records_ingested
FROM faculty_profiles
WHERE ingestion_timestamp IS NOT NULL
GROUP BY DATE(ingestion_timestamp)
ORDER BY ingestion_date DESC
LIMIT 30;

-- ============================================
-- QUESTION 8 : Course Sources
-- ============================================
SELECT 
    COALESCE(source_system, 'Unknown') AS data_source,
    COUNT(*) AS course_count
FROM course_catalog
GROUP BY source_system
ORDER BY course_count DESC;