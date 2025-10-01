from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class ExportBase(BaseModel):
    export_path: str = Field(..., description="Path where the .env file was exported")
    with_prefix: bool = Field(False, description="Whether to add prefix to variable names")
    with_suffix: bool = Field(False, description="Whether to add suffix to variable names")
    prefix_value: Optional[str] = Field(None, max_length=50, description="Prefix to add to variable names")
    suffix_value: Optional[str] = Field(None, max_length=50, description="Suffix to add to variable names")
    
    # Git tracking fields
    git_repo_path: Optional[str] = Field(None, description="Path to git repository root")
    git_branch: Optional[str] = Field(None, max_length=255, description="Git branch name")
    git_commit_hash: Optional[str] = Field(None, max_length=40, description="Git commit hash")
    git_remote_url: Optional[str] = Field(None, description="Git remote URL")
    is_git_repo: bool = Field(False, description="Whether export was in a git repository")


class ExportCreate(ExportBase):
    project_id: int = Field(..., description="ID of the project to export")


class ExportUpdate(BaseModel):
    export_path: Optional[str] = None
    with_prefix: Optional[bool] = None
    with_suffix: Optional[bool] = None
    prefix_value: Optional[str] = Field(None, max_length=50)
    suffix_value: Optional[str] = Field(None, max_length=50)


class ExportResponse(ExportBase):
    id: int
    project_id: int
    exported_at: datetime
    resolved_values: Dict[str, str] = Field(..., description="Resolved key-value pairs at export time")
    export_hash: Optional[str] = Field(None, description="Hash of resolved values for comparison")
    
    model_config = {"from_attributes": True}


class ExportListResponse(BaseModel):
    exports: List[ExportResponse]
    total: int
    page: int
    size: int


class ExportRequest(BaseModel):
    project_name: str = Field(..., description="Name of the project to export")
    out_dir: str = Field(..., description="Output directory for the .env file")
    with_prefix: bool = Field(False, description="Whether to add prefix to variable names")
    with_suffix: bool = Field(False, description="Whether to add suffix to variable names")
    prefix_value: Optional[str] = Field(None, max_length=50)
    suffix_value: Optional[str] = Field(None, max_length=50)


class ExportResult(BaseModel):
    success: bool
    export_path: str
    variables_exported: int
    message: str
    export_id: Optional[int] = None


class CheckUpdatesResponse(BaseModel):
    outdated_exports: List[Dict] = Field(..., description="List of exports that need updating")
    total_checked: int = Field(..., description="Total number of exports checked")
    outdated_count: int = Field(..., description="Number of outdated exports")


class DiffRequest(BaseModel):
    export_id: int = Field(..., description="ID of the export to compare against")


class DiffResponse(BaseModel):
    export_id: int
    export_path: str
    exported_at: datetime
    differences: List[Dict] = Field(..., description="List of variable differences")
    total_differences: int 