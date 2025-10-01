from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import logging

from ..core.database import get_db
from ..models import Project, EnvVar, EnvExport, ProjectLink
from ..schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectWithStats,
    ProjectListResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Projects"])


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    skip: int = Query(0, ge=0, description="Number of projects to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of projects to return"),
    db: AsyncSession = Depends(get_db)
):
    """List all projects with pagination"""
    try:
        # Get total count
        count_result = await db.execute(select(func.count(Project.id)))
        total = count_result.scalar()
        
        # Get projects with variable counts
        from sqlalchemy import func as sql_func
        result = await db.execute(
            select(
                Project,
                sql_func.count(EnvVar.id).label('variables_count')
            )
            .outerjoin(EnvVar, Project.id == EnvVar.project_id)
            .group_by(Project.id)
            .offset(skip)
            .limit(limit)
            .order_by(Project.name)
        )
        project_results = result.all()
        
        # Convert to ProjectResponse with variable count
        projects_with_stats = []
        for project, var_count in project_results:
            project_dict = ProjectResponse.model_validate(project).model_dump()
            project_dict['variables_count'] = var_count
            projects_with_stats.append(project_dict)
        
        return ProjectListResponse(
            projects=projects_with_stats,
            total=total,
            page=skip // limit + 1,
            size=limit
        )
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(status_code=500, detail="Failed to list projects")


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new project"""
    try:
        # Check if project with same name already exists
        existing = await db.execute(
            select(Project).where(Project.name == project.name)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail=f"Project with name '{project.name}' already exists"
            )
        
        # Create new project
        db_project = Project(
            name=project.name,
            description=project.description
        )
        db.add(db_project)
        await db.commit()
        await db.refresh(db_project)
        
        logger.info(f"Created project: {project.name}")
        return ProjectResponse.model_validate(db_project)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create project")


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific project by ID"""
    try:
        result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return ProjectResponse.model_validate(project)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get project")


@router.get("/{project_id}/stats", response_model=ProjectWithStats)
async def get_project_stats(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get project with statistics"""
    try:
        # Get project
        result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get variable count
        var_count_result = await db.execute(
            select(func.count(EnvVar.id)).where(EnvVar.project_id == project_id)
        )
        variable_count = var_count_result.scalar()
        
        # Get export count
        export_count_result = await db.execute(
            select(func.count(EnvExport.id)).where(EnvExport.project_id == project_id)
        )
        export_count = export_count_result.scalar()
        
        # Get linked projects
        linked_projects_result = await db.execute(
            select(Project.name)
            .join(ProjectLink, Project.id == ProjectLink.target_project_id)
            .where(ProjectLink.source_project_id == project_id)
        )
        linked_projects = [row[0] for row in linked_projects_result.fetchall()]
        
        # Create response
        response = ProjectResponse.model_validate(project)
        return ProjectWithStats(
            **response.model_dump(),
            variable_count=variable_count,
            export_count=export_count,
            linked_projects=linked_projects
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project stats {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get project stats")


@router.get("/dropdown/options")
async def get_project_dropdown_options(
    current_project_id: Optional[int] = Query(None, description="Current project ID (excluded from options)"),
    db: AsyncSession = Depends(get_db)
):
    """Get projects for dropdown selection (excluding current project)"""
    try:
        query = select(Project).order_by(Project.name)
        if current_project_id:
            query = query.where(Project.id != current_project_id)
        
        result = await db.execute(query)
        projects = result.scalars().all()
        
        return {
            "projects": [
                {
                    "id": project.id,
                    "name": project.name,
                    "description": project.description
                }
                for project in projects
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting project dropdown options: {e}")
        raise HTTPException(status_code=500, detail="Failed to get project options")


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a project"""
    try:
        # Get existing project
        result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        db_project = result.scalar_one_or_none()
        
        if not db_project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Check name uniqueness if name is being updated
        if project_update.name and project_update.name != db_project.name:
            existing = await db.execute(
                select(Project).where(Project.name == project_update.name)
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=400,
                    detail=f"Project with name '{project_update.name}' already exists"
                )
        
        # Update fields
        update_data = project_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_project, field, value)
        
        await db.commit()
        await db.refresh(db_project)
        
        logger.info(f"Updated project: {db_project.name}")
        return ProjectResponse.model_validate(db_project)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project {project_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update project")


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a project"""
    try:
        # Get project
        result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project_name = project.name
        
        # Delete project (cascade will handle related records)
        await db.delete(project)
        await db.commit()
        
        logger.info(f"Deleted project: {project_name}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete project") 