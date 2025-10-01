from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class VariableHistoryBase(BaseModel):
    """Base schema for variable history"""
    variable_name: str
    raw_value: Optional[str] = None
    linked_to: Optional[str] = None
    concat_parts: Optional[str] = None
    description: Optional[str] = None
    is_encrypted: bool = False
    change_type: str
    change_reason: Optional[str] = None
    changed_by: Optional[str] = None


class VariableHistoryCreate(VariableHistoryBase):
    """Schema for creating variable history entries"""
    env_var_id: int
    project_id: int


class VariableHistoryResponse(VariableHistoryBase):
    """Schema for variable history API responses"""
    id: int
    env_var_id: int
    project_id: int
    version_number: int
    created_at: datetime

    class Config:
        from_attributes = True


class VariableWithHistoryResponse(BaseModel):
    """Schema for variable with complete history"""
    current: dict
    history: List[VariableHistoryResponse]


class ProjectHistorySettingsUpdate(BaseModel):
    """Schema for updating project history settings"""
    history_limit: int = Field(..., ge=1, le=50, description="History limit between 1 and 50")
    confirm_cleanup: bool = Field(False, description="Confirm cleanup of excess history")


class ProjectHistorySettingsResponse(BaseModel):
    """Schema for project history settings response"""
    success: bool
    requires_confirmation: Optional[bool] = None
    warning: Optional[str] = None
    affected_variables: Optional[int] = None
    entries_to_remove: Optional[int] = None
    old_limit: Optional[int] = None
    new_limit: Optional[int] = None
    message: Optional[str] = None
    error: Optional[str] = None


class RestoreVariableRequest(BaseModel):
    """Schema for restoring a variable to a specific version"""
    version_number: int = Field(..., ge=1, description="Version number to restore to")
    change_reason: Optional[str] = Field(None, description="Reason for restoration")
    changed_by: Optional[str] = Field(None, description="User performing the restoration") 