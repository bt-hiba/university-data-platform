from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class FacultyResult(BaseModel):
    faculty_name: Optional[str] = None
    publication_title: Optional[str] = None
    publication_year: Optional[int] = None
    language: Optional[str] = None
    score: Optional[float] = None

    class Config:
        extra = "allow"

class CourseResult(BaseModel):
    course_name: Optional[str] = None
    faculty: Optional[str] = None
    description: Optional[str] = None

    class Config:
        extra = "allow"

class GlobalSearchResponse(BaseModel):
    faculty_profiles: List[Dict[str, Any]]
    course_catalog: List[Dict[str, Any]]