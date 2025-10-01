from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from ..core.database import get_db
from ..services.search_service import SearchService
from ..schemas.search import (
    SearchRequest, SearchResponse, SearchScope,
    SearchSuggestionsResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Search"])


@router.get("/", response_model=SearchResponse)
async def global_search(
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    scope: SearchScope = Query(SearchScope.EVERYTHING, description="Search scope"),
    project_id: Optional[int] = Query(None, description="Limit search to specific project"),
    limit: Optional[int] = Query(20, ge=1, le=100, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db)
):
    """Perform global search with fuzzy matching"""
    try:
        search_request = SearchRequest(
            query=q,
            scope=scope,
            project_id=project_id,
            limit=limit
        )
        
        search_service = SearchService(db)
        results = await search_service.global_search(search_request)
        
        logger.info(f"Search completed: '{q}' in {scope} scope, {results.total_results} results, {results.execution_time_ms}ms")
        return results
        
    except Exception as e:
        logger.error(f"Error performing search: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/suggestions", response_model=SearchSuggestionsResponse)
async def get_search_suggestions(
    q: str = Query(..., min_length=1, max_length=100, description="Search query for suggestions"),
    limit: Optional[int] = Query(5, ge=1, le=10, description="Maximum number of suggestions"),
    db: AsyncSession = Depends(get_db)
):
    """Get search suggestions for autocomplete"""
    try:
        search_service = SearchService(db)
        suggestions = await search_service.get_search_suggestions(q, limit)
        
        return suggestions
        
    except Exception as e:
        logger.error(f"Error getting search suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get suggestions")


@router.get("/projects")
async def search_projects_only(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: Optional[int] = Query(10, ge=1, le=50, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db)
):
    """Search projects only (simplified endpoint)"""
    try:
        search_service = SearchService(db)
        results = await search_service.search_projects(q, limit)
        
        return {"results": results}
        
    except Exception as e:
        logger.error(f"Error searching projects: {e}")
        raise HTTPException(status_code=500, detail="Project search failed")


@router.get("/variables")
async def search_variables_only(
    q: str = Query(..., min_length=1, description="Search query"),
    project_id: Optional[int] = Query(None, description="Limit to specific project"),
    limit: Optional[int] = Query(10, ge=1, le=50, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db)
):
    """Search environment variables only (simplified endpoint)"""
    try:
        search_service = SearchService(db)
        results = await search_service.search_variables(q, project_id, limit)
        
        return {"results": results}
        
    except Exception as e:
        logger.error(f"Error searching variables: {e}")
        raise HTTPException(status_code=500, detail="Variable search failed")


@router.get("/values")
async def search_values_only(
    q: str = Query(..., min_length=1, description="Search query"),
    project_id: Optional[int] = Query(None, description="Limit to specific project"),
    limit: Optional[int] = Query(10, ge=1, le=50, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db)
):
    """Search variable values only (simplified endpoint)"""
    try:
        search_service = SearchService(db)
        results = await search_service.search_values(q, project_id, limit)
        
        return {"results": results}
        
    except Exception as e:
        logger.error(f"Error searching values: {e}")
        raise HTTPException(status_code=500, detail="Value search failed") 