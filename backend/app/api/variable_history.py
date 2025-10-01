from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from ..core.database import get_db
from ..services.variable_history_service import VariableHistoryService
from ..schemas.variable_history import (
    VariableHistoryResponse, VariableWithHistoryResponse, 
    ProjectHistorySettingsUpdate, ProjectHistorySettingsResponse,
    RestoreVariableRequest
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Variable History"])


@router.get("/variable/{var_id}", response_model=List[VariableHistoryResponse])
async def get_variable_history(
    var_id: int,
    limit: Optional[int] = Query(None, description="Limit number of history entries"),
    db: AsyncSession = Depends(get_db)
):
    """Get history for a specific variable"""
    try:
        service = VariableHistoryService(db)
        history = await service.get_variable_history(var_id, limit)
        return [VariableHistoryResponse.model_validate(h.to_dict()) for h in history]
        
    except Exception as e:
        logger.error(f"Error getting variable history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/variable/{var_id}/with-current", response_model=VariableWithHistoryResponse)
async def get_variable_with_history(
    var_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get variable with its complete history"""
    try:
        service = VariableHistoryService(db)
        result = await service.get_variable_with_history(var_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Variable not found")
        
        return VariableWithHistoryResponse(
            current=result["current"],
            history=[VariableHistoryResponse.model_validate(h) for h in result["history"]]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting variable with history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/variable/{var_id}/restore")
async def restore_variable_version(
    var_id: int,
    request: RestoreVariableRequest,
    db: AsyncSession = Depends(get_db)
):
    """Restore a variable to a specific version"""
    try:
        service = VariableHistoryService(db)
        success = await service.restore_variable_version(
            var_id, 
            request.version_number,
            request.change_reason,
            request.changed_by
        )
        
        if not success:
            raise HTTPException(
                status_code=404, 
                detail=f"Variable or version {request.version_number} not found"
            )
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"Variable restored to version {request.version_number}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring variable version: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/project/{project_id}", response_model=List[VariableHistoryResponse])
async def get_project_history(
    project_id: int,
    limit: Optional[int] = Query(50, description="Limit number of history entries"),
    db: AsyncSession = Depends(get_db)
):
    """Get all history for a project"""
    try:
        service = VariableHistoryService(db)
        history = await service.get_project_history(project_id, limit)
        return [VariableHistoryResponse.model_validate(h.to_dict()) for h in history]
        
    except Exception as e:
        logger.error(f"Error getting project history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/project/{project_id}/settings", response_model=ProjectHistorySettingsResponse)
async def update_project_history_settings(
    project_id: int,
    request: ProjectHistorySettingsUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update project history settings"""
    try:
        service = VariableHistoryService(db)
        result = await service.update_project_history_settings(
            project_id,
            request.history_limit,
            request.confirm_cleanup
        )
        
        return ProjectHistorySettingsResponse(**result)
        
    except Exception as e:
        logger.error(f"Error updating project history settings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/project/{project_id}/settings")
async def get_project_history_settings(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get current project history settings"""
    try:
        from ..models import Project
        from sqlalchemy import select
        
        result = await db.execute(
            select(Project.history_enabled, Project.history_limit).where(
                Project.id == project_id
            )
        )
        settings = result.first()
        
        if not settings:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {
            "project_id": project_id,
            "history_enabled": settings.history_enabled,
            "history_limit": settings.history_limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project history settings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 