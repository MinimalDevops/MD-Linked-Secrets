from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Union, Dict
from datetime import datetime
import re


class EnvVarBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Variable name")
    description: Optional[str] = Field(None, description="Variable description")
    is_encrypted: bool = Field(False, description="Whether the value is encrypted")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None:
            # Check for spaces
            if ' ' in v:
                raise ValueError('Variable name cannot contain spaces')
            
            # Check for special characters (only allow letters, numbers, and underscores)
            if not re.match(r'^[A-Za-z0-9_]+$', v):
                raise ValueError('Variable name can only contain letters, numbers, and underscores')
            
            # Check if starts or ends with special character (underscore is allowed)
            if v.startswith('_') or v.endswith('_'):
                raise ValueError('Variable name cannot start or end with underscore')
            
            # Check if it's a valid variable name (should start with letter or underscore)
            if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', v):
                raise ValueError('Variable name must start with a letter or underscore')
        return v


class EnvVarCreate(EnvVarBase):
    project_id: int = Field(..., description="Project ID this variable belongs to")
    # Only one of these should be provided
    raw_value: Optional[str] = Field(None, description="Direct value")
    linked_to: Optional[str] = Field(None, description="Linked variable (PROJECT:VAR format)")
    concat_parts: Optional[str] = Field(None, description="Concatenated variables (\"PROJECT:VAR\" with optional separators)")
    
    @field_validator('linked_to')
    @classmethod
    def validate_linked_to(cls, v):
        if v is not None:
            if not re.match(r'^[A-Za-z0-9_-]+:[A-Za-z0-9_-]+$', v):
                raise ValueError('linked_to must be in format PROJECT:VAR')
        return v
    
    @field_validator('concat_parts')
    @classmethod
    def validate_concat_parts(cls, v):
        if v is not None:
            # Check for quoted format first: "PROJECT:VAR" with any separators
            quoted_pattern = r'^"[A-Za-z0-9_-]+:[A-Za-z0-9_-]+".*"[A-Za-z0-9_-]+:[A-Za-z0-9_-]+"$|^"[A-Za-z0-9_-]+:[A-Za-z0-9_-]+"$'
            # Allow old format for backward compatibility
            old_pattern = r'^[A-Za-z0-9_-]+:[A-Za-z0-9_-]+([^A-Za-z0-9_-]*[A-Za-z0-9_-]+:[A-Za-z0-9_-]+)*$'
            
            if not (re.match(quoted_pattern, v) or re.match(old_pattern, v)):
                raise ValueError('concat_parts must be in format "PROJECT:VAR" or PROJECT:VAR with optional separators')
        return v
    
    @model_validator(mode='before')
    @classmethod
    def validate_value_type(cls, data):
        if isinstance(data, dict):
            raw_value = data.get('raw_value')
            linked_to = data.get('linked_to')
            concat_parts = data.get('concat_parts')
            
            non_none_values = [val for val in [raw_value, linked_to, concat_parts] if val is not None]
            if len(non_none_values) > 1:
                raise ValueError('Only one of raw_value, linked_to, or concat_parts can be provided')
        return data


class EnvVarUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_encrypted: Optional[bool] = None
    raw_value: Optional[str] = None
    linked_to: Optional[str] = None
    concat_parts: Optional[str] = None
    
    @field_validator('linked_to')
    @classmethod
    def validate_linked_to(cls, v):
        if v is not None:
            if not re.match(r'^[A-Za-z0-9_-]+:[A-Za-z0-9_-]+$', v):
                raise ValueError('linked_to must be in format PROJECT:VAR')
        return v
    
    @field_validator('concat_parts')
    @classmethod
    def validate_concat_parts(cls, v):
        if v is not None:
            # Check for quoted format first: "PROJECT:VAR" with any separators
            quoted_pattern = r'^"[A-Za-z0-9_-]+:[A-Za-z0-9_-]+".*"[A-Za-z0-9_-]+:[A-Za-z0-9_-]+"$|^"[A-Za-z0-9_-]+:[A-Za-z0-9_-]+"$'
            # Allow old format for backward compatibility
            old_pattern = r'^[A-Za-z0-9_-]+:[A-Za-z0-9_-]+([^A-Za-z0-9_-]*[A-Za-z0-9_-]+:[A-Za-z0-9_-]+)*$'
            
            if not (re.match(quoted_pattern, v) or re.match(old_pattern, v)):
                raise ValueError('concat_parts must be in format "PROJECT:VAR" or PROJECT:VAR with optional separators')
        return v


class EnvVarResponse(EnvVarBase):
    id: int
    project_id: int
    raw_value: Optional[str] = None
    linked_to: Optional[str] = None
    concat_parts: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    value_type: str = Field(..., description="Type of value: raw, linked, concatenated, or empty")
    
    model_config = {"from_attributes": True}


class EnvVarWithResolvedValue(EnvVarResponse):
    resolved_value: Optional[str] = Field(None, description="Resolved value after linking/concatenation")
    resolution_errors: List[str] = Field(default_factory=list, description="Any errors during resolution")


class EnvVarListResponse(BaseModel):
    variables: List[EnvVarResponse]
    total: int
    page: int
    size: int


class VariableResolutionRequest(BaseModel):
    var_id: Optional[int] = Field(None, description="Variable ID to resolve")
    project_id: Optional[int] = Field(None, description="Project ID to resolve all variables for")
    include_resolved: bool = Field(True, description="Include resolved values in response")


class VariableResolutionResponse(BaseModel):
    resolved_values: Dict[str, str] = Field(..., description="Map of variable names to resolved values") 