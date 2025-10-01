from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, text
from sqlalchemy.orm import selectinload
import time
import re
from difflib import SequenceMatcher

from ..models import Project, EnvVar
from ..schemas.search import (
    SearchRequest, SearchResponse, SearchScope,
    ProjectSearchResult, VariableSearchResult, ValueSearchResult,
    SearchResultType, SearchSuggestion, SearchSuggestionsResponse
)


class SearchService:
    """Service for global search functionality with fuzzy matching"""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    def _calculate_similarity(self, query: str, text: str) -> float:
        """Calculate similarity score between query and text"""
        if not text:
            return 0.0
        
        query_lower = query.lower()
        text_lower = text.lower()
        
        # Exact match gets highest score
        if query_lower == text_lower:
            return 1.0
        
        # Check if query is a substring
        if query_lower in text_lower:
            # Score based on position and length ratio
            position = text_lower.find(query_lower)
            position_score = 1.0 - (position / len(text_lower))
            length_ratio = len(query_lower) / len(text_lower)
            return 0.8 + (0.2 * position_score * length_ratio)
        
        # Use SequenceMatcher for fuzzy matching
        similarity = SequenceMatcher(None, query_lower, text_lower).ratio()
        
        # Bonus for word boundaries
        words = text_lower.split()
        for word in words:
            if query_lower in word or word.startswith(query_lower):
                similarity += 0.1
                break
        
        return min(similarity, 1.0)
    
    def _highlight_match(self, query: str, text: str, max_length: int = 100) -> str:
        """Create highlighted match text with context"""
        if not text:
            return ""
        
        query_lower = query.lower()
        text_lower = text.lower()
        
        # Find the best match position
        if query_lower in text_lower:
            start_pos = text_lower.find(query_lower)
            end_pos = start_pos + len(query_lower)
            
            # Add context around the match
            context_start = max(0, start_pos - 20)
            context_end = min(len(text), end_pos + 20)
            
            prefix = "..." if context_start > 0 else ""
            suffix = "..." if context_end < len(text) else ""
            
            context_text = text[context_start:context_end]
            
            # Highlight the match (using simple markers for now)
            highlighted = text[context_start:start_pos] + f"**{text[start_pos:end_pos]}**" + text[end_pos:context_end]
            
            return f"{prefix}{highlighted}{suffix}"
        
        # If no exact match, return truncated text
        return text[:max_length] + ("..." if len(text) > max_length else "")
    
    async def search_projects(self, query: str, limit: int = 20) -> List[ProjectSearchResult]:
        """Search projects by name and description"""
        
        # Get all projects with variable counts
        query_stmt = select(
            Project.id,
            Project.name,
            Project.description,
            func.count(EnvVar.id).label('variables_count')
        ).outerjoin(EnvVar).group_by(
            Project.id, Project.name, Project.description
        )
        
        result = await self.db_session.execute(query_stmt)
        projects = result.all()
        
        # Calculate similarity scores and filter
        scored_projects = []
        for project in projects:
            # Check name similarity
            name_score = self._calculate_similarity(query, project.name)
            desc_score = self._calculate_similarity(query, project.description or "")
            
            best_score = max(name_score, desc_score)
            if best_score > 0.1:  # Minimum threshold
                match_field = "name" if name_score >= desc_score else "description"
                match_text = project.name if match_field == "name" else (project.description or "")
                
                scored_projects.append(ProjectSearchResult(
                    id=project.id,
                    name=project.name,
                    description=project.description,
                    variables_count=project.variables_count,
                    match_score=best_score,
                    match_field=match_field,
                    highlight=self._highlight_match(query, match_text)
                ))
        
        # Sort by score and return top results
        scored_projects.sort(key=lambda x: x.match_score, reverse=True)
        return scored_projects[:limit]
    
    async def search_variables(self, query: str, project_id: Optional[int] = None, limit: int = 20) -> List[VariableSearchResult]:
        """Search environment variables by name and description"""
        
        # Build query with optional project filter
        query_stmt = select(EnvVar, Project.name.label('project_name')).join(Project)
        
        if project_id:
            query_stmt = query_stmt.where(EnvVar.project_id == project_id)
        
        result = await self.db_session.execute(query_stmt)
        variables = result.all()
        
        # Calculate similarity scores
        scored_variables = []
        for var_row in variables:
            var = var_row.EnvVar
            project_name = var_row.project_name
            
            # Determine variable type
            value_type = "raw"
            if var.linked_to:
                value_type = "linked"
            elif var.concat_parts:
                value_type = "concatenated"
            
            # Check name and description similarity
            name_score = self._calculate_similarity(query, var.name)
            desc_score = self._calculate_similarity(query, var.description or "")
            
            best_score = max(name_score, desc_score)
            if best_score > 0.1:
                match_field = "name" if name_score >= desc_score else "description"
                match_text = var.name if match_field == "name" else (var.description or "")
                
                scored_variables.append(VariableSearchResult(
                    id=var.id,
                    name=var.name,
                    project_id=var.project_id,
                    project_name=project_name,
                    description=var.description,
                    value_type=value_type,
                    match_score=best_score,
                    match_field=match_field,
                    highlight=self._highlight_match(query, match_text)
                ))
        
        # Sort by score and return top results
        scored_variables.sort(key=lambda x: x.match_score, reverse=True)
        return scored_variables[:limit]
    
    async def search_values(self, query: str, project_id: Optional[int] = None, limit: int = 20) -> List[ValueSearchResult]:
        """Search environment variable values"""
        
        # Build query with optional project filter
        query_stmt = select(EnvVar, Project.name.label('project_name')).join(Project)
        
        if project_id:
            query_stmt = query_stmt.where(EnvVar.project_id == project_id)
        
        result = await self.db_session.execute(query_stmt)
        variables = result.all()
        
        # Calculate similarity scores for values
        scored_values = []
        for var_row in variables:
            var = var_row.EnvVar
            project_name = var_row.project_name
            
            # Determine variable type and value
            value_type = "raw"
            search_value = var.raw_value or ""
            
            if var.linked_to:
                value_type = "linked"
                search_value = var.linked_to
            elif var.concat_parts:
                value_type = "concatenated"
                search_value = var.concat_parts
            
            # Check value similarity
            value_score = self._calculate_similarity(query, search_value)
            
            if value_score > 0.1:
                # Create preview (truncated value)
                value_preview = search_value[:50] + ("..." if len(search_value) > 50 else "")
                
                scored_values.append(ValueSearchResult(
                    id=var.id,
                    variable_name=var.name,
                    project_id=var.project_id,
                    project_name=project_name,
                    value_preview=value_preview,
                    value_type=value_type,
                    match_score=value_score,
                    match_field="value",
                    highlight=self._highlight_match(query, search_value, 80)
                ))
        
        # Sort by score and return top results
        scored_values.sort(key=lambda x: x.match_score, reverse=True)
        return scored_values[:limit]
    
    async def global_search(self, request: SearchRequest) -> SearchResponse:
        """Perform global search across all scopes"""
        start_time = time.time()
        all_results: List[SearchResultType] = []
        
        if request.scope == SearchScope.EVERYTHING:
            # Search all scopes
            projects = await self.search_projects(request.query, request.limit // 3)
            variables = await self.search_variables(request.query, request.project_id, request.limit // 3)
            values = await self.search_values(request.query, request.project_id, request.limit // 3)
            
            all_results.extend(projects)
            all_results.extend(variables)
            all_results.extend(values)
            
        elif request.scope == SearchScope.PROJECTS:
            projects = await self.search_projects(request.query, request.limit)
            all_results.extend(projects)
            
        elif request.scope == SearchScope.ENV_VARS:
            variables = await self.search_variables(request.query, request.project_id, request.limit)
            all_results.extend(variables)
            
        elif request.scope == SearchScope.VALUES:
            values = await self.search_values(request.query, request.project_id, request.limit)
            all_results.extend(values)
        
        # Sort all results by score
        all_results.sort(key=lambda x: x.match_score, reverse=True)
        
        # Limit final results
        final_results = all_results[:request.limit]
        
        execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return SearchResponse(
            query=request.query,
            scope=request.scope,
            project_id=request.project_id,
            total_results=len(final_results),
            results=final_results,
            execution_time_ms=round(execution_time, 2)
        )
    
    async def get_search_suggestions(self, query: str, limit: int = 5) -> SearchSuggestionsResponse:
        """Get search suggestions for autocomplete"""
        suggestions = []
        
        if len(query) >= 2:
            # Get project name suggestions
            project_stmt = select(Project.name).where(
                Project.name.ilike(f"%{query}%")
            ).limit(limit)
            
            project_result = await self.db_session.execute(project_stmt)
            project_names = project_result.scalars().all()
            
            for name in project_names:
                suggestions.append(SearchSuggestion(
                    text=name,
                    type="project"
                ))
            
            # Get variable name suggestions
            var_stmt = select(EnvVar.name).where(
                EnvVar.name.ilike(f"%{query}%")
            ).distinct().limit(limit)
            
            var_result = await self.db_session.execute(var_stmt)
            var_names = var_result.scalars().all()
            
            for name in var_names:
                suggestions.append(SearchSuggestion(
                    text=name,
                    type="variable"
                ))
        
        return SearchSuggestionsResponse(suggestions=suggestions[:limit]) 