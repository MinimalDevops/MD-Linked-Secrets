from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Union
from enum import Enum


class SearchScope(str, Enum):
    """Search scope options"""
    EVERYTHING = "everything"
    PROJECTS = "projects"
    ENV_VARS = "env_vars"
    VALUES = "values"


class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    scope: SearchScope = Field(SearchScope.EVERYTHING, description="Search scope")
    project_id: Optional[int] = Field(None, description="Limit search to specific project (for env_vars and values)")
    limit: Optional[int] = Field(20, ge=1, le=100, description="Maximum number of results")


class ProjectSearchResult(BaseModel):
    """Project search result"""
    type: Literal["project"] = "project"
    id: int
    name: str
    description: Optional[str]
    variables_count: int
    match_score: float
    match_field: str  # "name" or "description"
    highlight: str  # Highlighted match text


class VariableSearchResult(BaseModel):
    """Environment variable search result"""
    type: Literal["variable"] = "variable"
    id: int
    name: str
    project_id: int
    project_name: str
    description: Optional[str]
    value_type: str  # "raw", "linked", "concatenated"
    match_score: float
    match_field: str  # "name" or "description"
    highlight: str


class ValueSearchResult(BaseModel):
    """Variable value search result"""
    type: Literal["value"] = "value"
    id: int
    variable_name: str
    project_id: int
    project_name: str
    value_preview: str  # Truncated value for preview
    value_type: str
    match_score: float
    match_field: str  # "value"
    highlight: str


SearchResultType = Union[ProjectSearchResult, VariableSearchResult, ValueSearchResult]


class SearchResponse(BaseModel):
    """Search response model"""
    query: str
    scope: SearchScope
    project_id: Optional[int]
    total_results: int
    results: List[SearchResultType]
    execution_time_ms: float


class SearchSuggestion(BaseModel):
    """Search suggestion for autocomplete"""
    text: str
    type: str  # "project", "variable", "recent"
    count: Optional[int] = None


class SearchSuggestionsResponse(BaseModel):
    """Search suggestions response"""
    suggestions: List[SearchSuggestion] 