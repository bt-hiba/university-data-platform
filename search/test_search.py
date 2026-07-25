from search.search_queries import (
    search_faculty,
    search_courses,
    search_everything
)

print("=" * 60)
print("Faculty Search")
print("=" * 60)

print(search_faculty("biofungicides"))

print()

print("=" * 60)
print("Course Search")
print("=" * 60)

print(search_courses("machine"))

print()

print("=" * 60)
print("Global Search")
print("=" * 60)

print(search_everything("machine"))