from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, description="Project description")


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime
    variables_count: Optional[int] = Field(0, description="Number of environment variables")
    
    model_config = {"from_attributes": True}


class ProjectWithStats(ProjectResponse):
    variable_count: int = Field(..., description="Number of environment variables")
    export_count: int = Field(..., description="Number of exports")
    linked_projects: List[str] = Field(default_factory=list, description="Names of linked projects")


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int
    page: int
    size: int 