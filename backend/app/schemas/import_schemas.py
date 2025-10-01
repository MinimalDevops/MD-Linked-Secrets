from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class EnvFileImportRequest(BaseModel):
    """Request model for importing .env file content"""
    project_id: int = Field(..., description="Target project ID")
    env_content: str = Field(..., description="Content of the .env file")
    overwrite_existing: bool = Field(False, description="Whether to overwrite existing variables")
    strip_prefix: Optional[str] = Field(None, description="Prefix to strip from variable names")
    strip_suffix: Optional[str] = Field(None, description="Suffix to strip from variable names")
    add_prefix: Optional[str] = Field(None, description="Prefix to add to variable names")
    add_suffix: Optional[str] = Field(None, description="Suffix to add to variable names")
    conflict_resolutions: Optional[Dict[str, str]] = Field(None, description="Individual conflict resolutions {var_name: 'skip'|'overwrite'}")
    description: Optional[str] = Field(None, description="Custom description for imported variables")


class ParsedEnvVariable(BaseModel):
    """Parsed variable from .env file"""
    name: str
    value: str
    original_name: str  # Before any prefix/suffix transformations
    line_number: int


class ImportConflict(BaseModel):
    """Represents a conflict during import"""
    variable_name: str
    existing_value: Optional[str]
    new_value: str
    existing_type: str  # 'raw', 'linked', 'concatenated'
    action: str  # 'skip', 'overwrite', 'rename'


class EnvImportPreview(BaseModel):
    """Preview of what will be imported"""
    total_variables: int
    new_variables: List[ParsedEnvVariable]
    conflicts: List[ImportConflict]
    skipped_lines: List[str]
    warnings: List[str]


class EnvImportResult(BaseModel):
    """Result of import operation"""
    success: bool
    import_id: Optional[int]
    variables_imported: int
    variables_skipped: int
    variables_overwritten: int
    conflicts_resolved: int
    errors: List[str]
    warnings: List[str]
    message: str


class EnvImportRecord(BaseModel):
    """Database record of import operation"""
    id: int
    project_id: int
    import_source: str  # 'file_upload', 'cli', 'api'
    imported_at: datetime
    variables_imported: int
    variables_skipped: int
    variables_overwritten: int
    import_hash: str
    created_at: datetime 