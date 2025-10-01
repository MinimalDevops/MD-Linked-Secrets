from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
import logging

from ..core.database import get_db
from ..core.variable_resolver import VariableResolver
from ..services.variable_history_service import VariableHistoryService
from ..models import EnvVar, Project
from ..schemas.env_var import (
    EnvVarCreate,
    EnvVarUpdate,
    EnvVarResponse,
    EnvVarWithResolvedValue,
    EnvVarListResponse,
    VariableResolutionRequest,
    VariableResolutionResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Environment Variables"])


@router.get("/", response_model=EnvVarListResponse)
async def list_env_vars(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """List environment variables with optional filtering"""
    try:
        # Build query
        query = select(EnvVar).join(Project)
        if project_id:
            query = query.where(EnvVar.project_id == project_id)
        
        # Get total count
        count_query = select(EnvVar)
        if project_id:
            count_query = count_query.where(EnvVar.project_id == project_id)
        total_result = await db.execute(count_query)
        total = len(total_result.scalars().all())
        
        # Get paginated results
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        env_vars = result.scalars().all()
        
        return EnvVarListResponse(
            variables=[EnvVarResponse.model_validate(var) for var in env_vars],
            total=total,
            page=skip // limit + 1,
            size=limit
        )
        
    except Exception as e:
        logger.error(f"Error listing environment variables: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=EnvVarResponse)
async def create_env_var(
    env_var: EnvVarCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new environment variable"""
    try:
        # Check if project exists
        project_result = await db.execute(
            select(Project).where(Project.id == env_var.project_id)
        )
        project = project_result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Check if variable name already exists in project
        existing_result = await db.execute(
            select(EnvVar).where(
                and_(EnvVar.project_id == env_var.project_id, EnvVar.name == env_var.name)
            )
        )
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=400, 
                detail=f"Variable '{env_var.name}' already exists in project '{project.name}'"
            )
        
        # Validate variable references if needed
        resolver = VariableResolver(db)
        validation_errors = await resolver.validate_variable_references(env_var)
        if validation_errors:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid variable references: {', '.join(validation_errors)}"
            )
        
        # Additional validation for linked variables - ensure they exist
        if env_var.linked_to:
            project_name, var_name = env_var.linked_to.split(':', 1)
            
            # Check if the referenced project exists
            project_result = await db.execute(
                select(Project).where(Project.name == project_name)
            )
            referenced_project = project_result.scalar_one_or_none()
            
            if not referenced_project:
                raise HTTPException(
                    status_code=400,
                    detail=f"Referenced project '{project_name}' does not exist"
                )
            
            # Check if the referenced variable exists
            var_result = await db.execute(
                select(EnvVar).where(
                    and_(EnvVar.project_id == referenced_project.id, EnvVar.name == var_name)
                )
            )
            referenced_var = var_result.scalar_one_or_none()
            
            if not referenced_var:
                raise HTTPException(
                    status_code=400,
                    detail=f"Referenced variable '{var_name}' does not exist in project '{project_name}'"
                )
            
            # Check that linked variables can only reference raw or concatenated variables
            if referenced_var.linked_to is not None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot link to variable '{var_name}' in project '{project_name}' because it is a linked variable. Only raw and concatenated variables can be referenced."
                )
        
        # Additional validation for concatenated variables - only allow current project variables
        if env_var.concat_parts:
            # Use the same parsing logic as the variable resolver
            import re
            
            # First try to find quoted PROJECT:VAR patterns
            quoted_parts = re.findall(r'"([A-Za-z0-9_-]+:[A-Za-z0-9_-]+)"', env_var.concat_parts)
            
            if quoted_parts:
                # Use quoted format
                parts = quoted_parts
            else:
                # Fallback to old format for backward compatibility
                parts = env_var.concat_parts.split('|')
            
            for part in parts:
                if ':' not in part:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Concatenation part '{part}' must be in format PROJECT:VAR"
                    )
                
                project_name, var_name = part.split(':', 1)
                
                # For concatenation, only allow variables from the current project
                if project_name != project.name:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Concatenation can only reference variables from the current project '{project.name}', not '{project_name}'"
                    )
                
                # Check if the referenced variable exists in current project
                var_result = await db.execute(
                    select(EnvVar).where(
                        and_(EnvVar.project_id == project.id, EnvVar.name == var_name)
                    )
                )
                referenced_var = var_result.scalar_one_or_none()
                
                if not referenced_var:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Referenced variable '{var_name}' does not exist in current project '{project.name}'"
                    )
        
        # Create the variable
        db_env_var = EnvVar(**env_var.model_dump())
        db.add(db_env_var)
        await db.commit()
        await db.refresh(db_env_var)
        
        # Create history entry
        history_service = VariableHistoryService(db)
        await history_service.create_history_entry(
            db_env_var, 
            "created", 
            "Variable created via API",
            "api_user"  # TODO: Replace with actual user when auth is implemented
        )
        await db.commit()
        
        logger.info(f"Created environment variable: {db_env_var.name} in project: {project.name}")
        return EnvVarResponse.model_validate(db_env_var)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating environment variable: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{var_id}", response_model=EnvVarResponse)
async def get_env_var(
    var_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific environment variable by ID"""
    try:
        result = await db.execute(
            select(EnvVar).where(EnvVar.id == var_id)
        )
        env_var = result.scalar_one_or_none()
        
        if not env_var:
            raise HTTPException(status_code=404, detail="Environment variable not found")
        
        return EnvVarResponse.model_validate(env_var)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting environment variable: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{var_id}", response_model=EnvVarResponse)
async def update_env_var(
    var_id: int,
    env_var_update: EnvVarUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an environment variable"""
    try:
        # Get existing variable
        result = await db.execute(
            select(EnvVar).where(EnvVar.id == var_id)
        )
        db_env_var = result.scalar_one_or_none()
        
        if not db_env_var:
            raise HTTPException(status_code=404, detail="Environment variable not found")
        
        # Check name uniqueness if name is being updated
        if env_var_update.name and env_var_update.name != db_env_var.name:
            existing_result = await db.execute(
                select(EnvVar).where(
                    and_(
                        EnvVar.project_id == db_env_var.project_id,
                        EnvVar.name == env_var_update.name,
                        EnvVar.id != var_id
                    )
                )
            )
            if existing_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=400,
                    detail=f"Variable name '{env_var_update.name}' already exists in this project"
                )
        
        # Update fields
        update_data = env_var_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_env_var, field, value)
        
        await db.commit()
        await db.refresh(db_env_var)
        
        # Create history entry
        history_service = VariableHistoryService(db)
        await history_service.create_history_entry(
            db_env_var, 
            "updated", 
            "Variable updated via API",
            "api_user"  # TODO: Replace with actual user when auth is implemented
        )
        await db.commit()
        
        logger.info(f"Updated environment variable: {db_env_var.name}")
        return EnvVarResponse.model_validate(db_env_var)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating environment variable: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{var_id}")
async def delete_env_var(
    var_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete an environment variable"""
    try:
        # Get existing variable
        result = await db.execute(
            select(EnvVar).where(EnvVar.id == var_id)
        )
        db_env_var = result.scalar_one_or_none()
        
        if not db_env_var:
            raise HTTPException(status_code=404, detail="Environment variable not found")
        
        # Check if other variables depend on this one
        resolver = VariableResolver(db)
        dependent_vars = await resolver._get_dependent_variables(var_id)
        
        if dependent_vars:
            dependent_names = [var.name for var in dependent_vars]
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete variable '{db_env_var.name}' as it is referenced by: {', '.join(dependent_names)}"
            )
        
        # Create history entry before deletion
        history_service = VariableHistoryService(db)
        await history_service.create_history_entry(
            db_env_var, 
            "deleted", 
            "Variable deleted via API",
            "api_user"  # TODO: Replace with actual user when auth is implemented
        )
        
        # Delete the variable
        await db.delete(db_env_var)
        await db.commit()
        
        logger.info(f"Deleted environment variable: {db_env_var.name}")
        return {"message": "Environment variable deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting environment variable: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{var_id}/change-type", response_model=EnvVarResponse)
async def change_variable_type(
    var_id: int,
    env_var_update: EnvVarUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Change variable type by deleting current variable and creating a new one"""
    try:
        # Get existing variable
        result = await db.execute(
            select(EnvVar).where(EnvVar.id == var_id)
        )
        db_env_var = result.scalar_one_or_none()
        
        if not db_env_var:
            raise HTTPException(status_code=404, detail="Environment variable not found")
        
        # Get project info
        project_result = await db.execute(
            select(Project).where(Project.id == db_env_var.project_id)
        )
        project = project_result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Determine the new variable type based on the update data
        new_type = None
        if env_var_update.raw_value is not None:
            new_type = "raw"
        elif env_var_update.linked_to is not None:
            new_type = "linked"
        elif env_var_update.concat_parts is not None:
            new_type = "concatenated"
        else:
            raise HTTPException(
                status_code=400,
                detail="Must provide one of: raw_value, linked_to, or concat_parts"
            )
        
        # Determine current variable type
        current_type = db_env_var.value_type
        
        # If the type is not actually changing, use regular update
        if new_type == current_type:
            # Use the regular update endpoint logic
            update_data = env_var_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_env_var, field, value)
            
            await db.commit()
            await db.refresh(db_env_var)
            
            # Create history entry
            history_service = VariableHistoryService(db)
            await history_service.create_history_entry(
                db_env_var, 
                "updated", 
                "Variable updated via API",
                "api_user"
            )
            await db.commit()
            
            logger.info(f"Updated environment variable: {db_env_var.name}")
            return EnvVarResponse.model_validate(db_env_var)
        
        # Check name uniqueness if name is being updated
        new_name = env_var_update.name if env_var_update.name else db_env_var.name
        if new_name != db_env_var.name:
            existing_result = await db.execute(
                select(EnvVar).where(
                    and_(
                        EnvVar.project_id == db_env_var.project_id,
                        EnvVar.name == new_name,
                        EnvVar.id != var_id
                    )
                )
            )
            if existing_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=400,
                    detail=f"Variable name '{new_name}' already exists in this project"
                )
        
        # Validate variable references for the new type
        resolver = VariableResolver(db)
        
        # Create a temporary object for validation
        temp_var_data = {
            "project_id": db_env_var.project_id,
            "name": new_name,
            "description": env_var_update.description if env_var_update.description is not None else db_env_var.description,
            "is_encrypted": env_var_update.is_encrypted if env_var_update.is_encrypted is not None else db_env_var.is_encrypted,
            "raw_value": env_var_update.raw_value,
            "linked_to": env_var_update.linked_to,
            "concat_parts": env_var_update.concat_parts,
        }
        
        # Validate variable references if needed
        validation_errors = await resolver.validate_variable_references(temp_var_data)
        if validation_errors:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid variable references: {', '.join(validation_errors)}"
            )
        
        # Additional validation for linked variables - ensure they exist
        if env_var_update.linked_to:
            project_name, var_name = env_var_update.linked_to.split(':', 1)
            
            # Check if the referenced project exists
            project_result = await db.execute(
                select(Project).where(Project.name == project_name)
            )
            referenced_project = project_result.scalar_one_or_none()
            
            if not referenced_project:
                raise HTTPException(
                    status_code=400,
                    detail=f"Referenced project '{project_name}' does not exist"
                )
            
            # Check if the referenced variable exists
            var_result = await db.execute(
                select(EnvVar).where(
                    and_(EnvVar.project_id == referenced_project.id, EnvVar.name == var_name)
                )
            )
            referenced_var = var_result.scalar_one_or_none()
            
            if not referenced_var:
                raise HTTPException(
                    status_code=400,
                    detail=f"Referenced variable '{var_name}' does not exist in project '{project_name}'"
                )
            
            # Check that linked variables can only reference raw or concatenated variables
            if referenced_var.linked_to is not None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot link to variable '{var_name}' in project '{project_name}' because it is a linked variable. Only raw and concatenated variables can be referenced."
                )
        
        # Additional validation for concatenated variables - only allow current project variables
        if env_var_update.concat_parts:
            # Use the same parsing logic as the variable resolver
            import re
            
            # First try to find quoted PROJECT:VAR patterns
            quoted_parts = re.findall(r'"([A-Za-z0-9_-]+:[A-Za-z0-9_-]+)"', env_var_update.concat_parts)
            
            if quoted_parts:
                # Use quoted format
                parts = quoted_parts
            else:
                # Fallback to old format for backward compatibility
                parts = env_var_update.concat_parts.split('|')
            
            for part in parts:
                if ':' not in part:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Concatenation part '{part}' must be in format PROJECT:VAR"
                    )
                
                project_name, var_name = part.split(':', 1)
                
                # For concatenation, only allow variables from the current project
                if project_name != project.name:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Concatenation can only reference variables from the current project '{project.name}', not '{project_name}'"
                    )
                
                # Check if the referenced variable exists in current project
                var_result = await db.execute(
                    select(EnvVar).where(
                        and_(EnvVar.project_id == project.id, EnvVar.name == var_name)
                    )
                )
                referenced_var = var_result.scalar_one_or_none()
                
                if not referenced_var:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Referenced variable '{var_name}' does not exist in current project '{project.name}'"
                    )
        
        # Check if other variables depend on this one
        dependent_vars = await resolver._get_dependent_variables(var_id)
        
        if dependent_vars:
            dependent_names = [var.name for var in dependent_vars]
            raise HTTPException(
                status_code=400,
                detail=f"Cannot change type of variable '{db_env_var.name}' as it is referenced by: {', '.join(dependent_names)}"
            )
        
        # Create history entry for deletion
        history_service = VariableHistoryService(db)
        await history_service.create_history_entry(
            db_env_var, 
            "deleted", 
            f"Variable deleted during type change from {current_type} to {new_type}",
            "api_user"
        )
        
        # Store the old variable data for history
        old_var_data = {
            "id": db_env_var.id,
            "name": db_env_var.name,
            "project_id": db_env_var.project_id,
            "raw_value": db_env_var.raw_value,
            "linked_to": db_env_var.linked_to,
            "concat_parts": db_env_var.concat_parts,
            "description": db_env_var.description,
            "is_encrypted": db_env_var.is_encrypted,
        }
        
        # Delete the old variable
        await db.delete(db_env_var)
        await db.commit()
        
        # Create the new variable with the new type
        new_var_data = {
            "project_id": old_var_data["project_id"],
            "name": new_name,
            "description": env_var_update.description if env_var_update.description is not None else old_var_data["description"],
            "is_encrypted": env_var_update.is_encrypted if env_var_update.is_encrypted is not None else old_var_data["is_encrypted"],
            "raw_value": env_var_update.raw_value,
            "linked_to": env_var_update.linked_to,
            "concat_parts": env_var_update.concat_parts,
        }
        
        # Clear the fields that don't apply to the new type
        if new_type == "raw":
            new_var_data["linked_to"] = None
            new_var_data["concat_parts"] = None
        elif new_type == "linked":
            new_var_data["raw_value"] = None
            new_var_data["concat_parts"] = None
        elif new_type == "concatenated":
            new_var_data["raw_value"] = None
            new_var_data["linked_to"] = None
        
        new_env_var = EnvVar(**new_var_data)
        db.add(new_env_var)
        await db.commit()
        await db.refresh(new_env_var)
        
        # Create history entry for the new variable
        await history_service.create_history_entry(
            new_env_var, 
            "created", 
            f"Variable created during type change from {current_type} to {new_type}",
            "api_user"
        )
        await db.commit()
        
        logger.info(f"Changed variable type: {old_var_data['name']} from {current_type} to {new_type}")
        return EnvVarResponse.model_validate(new_env_var)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing variable type: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/resolve", response_model=VariableResolutionResponse)
async def resolve_variables(
    request: VariableResolutionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Resolve environment variables for a project"""
    try:
        resolver = VariableResolver(db)
        
        if request.var_id:
            # Resolve single variable
            resolved_value = await resolver.resolve_variable(request.var_id)
            if resolved_value is None:
                raise HTTPException(status_code=404, detail="Variable not found")
            
            return VariableResolutionResponse(
                resolved_values={str(request.var_id): resolved_value}
            )
        elif request.project_id:
            # Resolve all variables for project
            resolved_values = await resolver.resolve_project_variables(request.project_id)
            return VariableResolutionResponse(resolved_values=resolved_values)
        else:
            raise HTTPException(
                status_code=400,
                detail="Either var_id or project_id must be provided"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving variables: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{var_id}/affected-exports")
async def get_affected_exports(
    var_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all exports that would be affected by a change to this variable"""
    try:
        resolver = VariableResolver(db)
        affected_exports = await resolver.get_affected_exports(var_id)
        
        return {
            "var_id": var_id,
            "affected_exports": affected_exports,
            "count": len(affected_exports)
        }
        
    except Exception as e:
        logger.error(f"Error getting affected exports: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{var_id}/impact-analysis")
async def get_variable_impact_analysis(
    var_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive analysis of what would be affected by updating this variable"""
    try:
        # Get the variable being analyzed
        result = await db.execute(
            select(EnvVar).where(EnvVar.id == var_id)
        )
        source_var = result.scalar_one_or_none()
        
        if not source_var:
            raise HTTPException(status_code=404, detail="Environment variable not found")
        
        # Get the source project
        project_result = await db.execute(
            select(Project).where(Project.id == source_var.project_id)
        )
        source_project = project_result.scalar_one_or_none()
        
        if not source_project:
            raise HTTPException(status_code=404, detail="Source project not found")
        
        # Use the resolver to get dependent variables
        resolver = VariableResolver(db)
        dependent_vars = await resolver._get_dependent_variables(var_id)
        
        # Group dependent variables by project
        projects_affected = {}
        
        for dep_var in dependent_vars:
            # Get the project for this dependent variable
            dep_project_result = await db.execute(
                select(Project).where(Project.id == dep_var.project_id)
            )
            dep_project = dep_project_result.scalar_one_or_none()
            
            if dep_project:
                project_name = dep_project.name
                if project_name not in projects_affected:
                    projects_affected[project_name] = {
                        "project_id": dep_project.id,
                        "project_name": project_name,
                        "project_description": dep_project.description,
                        "variables": []
                    }
                
                # Determine variable type
                var_type = "raw" if dep_var.raw_value else "linked" if dep_var.linked_to else "concatenated"
                
                projects_affected[project_name]["variables"].append({
                    "id": dep_var.id,
                    "name": dep_var.name,
                    "type": var_type,
                    "description": dep_var.description,
                    "reference": dep_var.linked_to or dep_var.concat_parts,
                    "created_at": dep_var.created_at.isoformat() if dep_var.created_at else None,
                    "updated_at": dep_var.updated_at.isoformat() if dep_var.updated_at else None
                })
        
        # Get affected exports
        affected_exports = await resolver.get_affected_exports(var_id)
        
        # Calculate summary statistics
        total_projects_affected = len(projects_affected)
        total_variables_affected = len(dependent_vars)
        total_exports_affected = len(affected_exports)
        
        return {
            "source_variable": {
                "id": source_var.id,
                "name": source_var.name,
                "project_id": source_project.id,
                "project_name": source_project.name,
                "type": "raw" if source_var.raw_value else "linked" if source_var.linked_to else "concatenated",
                "description": source_var.description
            },
            "impact_summary": {
                "total_projects_affected": total_projects_affected,
                "total_variables_affected": total_variables_affected,
                "total_exports_affected": total_exports_affected,
                "has_cross_project_impact": any(
                    proj_data["project_id"] != source_project.id 
                    for proj_data in projects_affected.values()
                )
            },
            "affected_projects": list(projects_affected.values()),
            "affected_exports": affected_exports,
            "recommendations": [
                "Review all affected variables before making changes",
                "Consider the impact on other projects" if total_projects_affected > 1 else "Impact is contained within current project",
                "Update affected exports after changes" if total_exports_affected > 0 else "No exports will be affected",
                "Test dependent variables after making changes" if total_variables_affected > 0 else "No dependent variables found"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting variable impact analysis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/dropdown/options")
async def get_variable_dropdown_options(
    project_id: int = Query(..., description="Project ID to get variables for"),
    db: AsyncSession = Depends(get_db)
):
    """Get variables for dropdown selection from a specific project (for linking)"""
    try:
        # Check if project exists
        project_result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project_result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get variables for the project (only raw and concatenated for linking)
        result = await db.execute(
            select(EnvVar).where(
                and_(
                    EnvVar.project_id == project_id,
                    EnvVar.linked_to.is_(None)  # Only raw and concatenated variables
                )
            ).order_by(EnvVar.name)
        )
        variables = result.scalars().all()
        
        return {
            "project": {
                "id": project.id,
                "name": project.name
            },
            "variables": [
                {
                    "id": var.id,
                    "name": var.name,
                    "description": var.description,
                    "value_type": "raw" if var.raw_value else "linked" if var.linked_to else "concatenated"
                }
                for var in variables
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting variable dropdown options: {e}")
        raise HTTPException(status_code=500, detail="Failed to get variable options")


@router.get("/concatenation/options")
async def get_concatenation_variable_options(
    project_id: int = Query(..., description="Project ID to get variables for concatenation"),
    db: AsyncSession = Depends(get_db)
):
    """Get all variables from a project for concatenation (including linked and concatenated)"""
    try:
        # Check if project exists
        project_result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project_result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get all variables for the project (including linked and concatenated for concatenation)
        result = await db.execute(
            select(EnvVar).where(EnvVar.project_id == project_id).order_by(EnvVar.name)
        )
        variables = result.scalars().all()
        
        return {
            "project": {
                "id": project.id,
                "name": project.name
            },
            "variables": [
                {
                    "id": var.id,
                    "name": var.name,
                    "description": var.description,
                    "value_type": "raw" if var.raw_value else "linked" if var.linked_to else "concatenated"
                }
                for var in variables
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting concatenation variable options: {e}")
        raise HTTPException(status_code=500, detail="Failed to get concatenation variable options") 