from fastapi import APIRouter, Query
from typing import List, Dict, Any
from search import search_queries
from api.schemas import GlobalSearchResponse

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("/faculty", response_model=List[Dict[str, Any]])
def search_faculty(q: str = Query(..., description="Query text to search in faculty profiles")):
    return search_queries.search_faculty(q)

@router.get("/course", response_model=List[Dict[str, Any]])
def search_courses(q: str = Query(..., description="Query text to search in course catalog")):
    return search_queries.search_courses(q)

@router.get("/all", response_model=GlobalSearchResponse)
def global_search(q: str = Query(..., description="Global search query across all indices")):
    return search_queries.search_everything(q)

@router.get("/language", response_model=List[Dict[str, Any]])
def search_by_language(language: str = Query(..., description="Language filter (e.g. en, fr)")):
    return search_queries.search_by_language(language)

@router.get("/year", response_model=List[Dict[str, Any]])
def search_by_year(year: int = Query(..., description="Publication year filter (e.g. 2024)")):
    return search_queries.search_by_year(year)