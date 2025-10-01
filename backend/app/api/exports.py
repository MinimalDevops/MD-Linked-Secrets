from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional, Dict, Tuple
import logging
import hashlib
import json
import subprocess
import os
from pathlib import Path
from datetime import datetime

from ..core.database import get_db
from ..core.variable_resolver import VariableResolver
from ..models import EnvExport, Project, EnvVar
from ..schemas.export import (
    ExportCreate,
    ExportUpdate,
    ExportResponse,
    ExportListResponse,
    ExportRequest,
    ExportResult,
    CheckUpdatesResponse,
    DiffRequest,
    DiffResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Exports"])


def get_git_info(export_path: str) -> Dict[str, Optional[str]]:
    """Get git repository information for a given export path"""
    git_info = {
        "git_repo_path": None,
        "git_branch": None,
        "git_commit_hash": None,
        "git_remote_url": None,
        "is_git_repo": False
    }
    
    try:
        export_path_obj = Path(export_path).resolve()
        
        # Find git repository root
        current_path = export_path_obj.parent
        git_root = None
        
        while current_path != current_path.parent:  # Not at filesystem root
            if (current_path / ".git").exists():
                git_root = current_path
                break
            current_path = current_path.parent
        
        if not git_root:
            return git_info
        
        git_info["is_git_repo"] = True
        git_info["git_repo_path"] = str(git_root)
        
        # Get current branch
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=git_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                git_info["git_branch"] = result.stdout.strip()
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        # Get current commit hash
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=git_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                git_info["git_commit_hash"] = result.stdout.strip()
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        # Get remote URL
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=git_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                git_info["git_remote_url"] = result.stdout.strip()
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            pass
            
    except Exception as e:
        logger.warning(f"Failed to get git info for {export_path}: {e}")
    
    return git_info


@router.get("/", response_model=ExportListResponse)
async def list_exports(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    git_branch: Optional[str] = Query(None, description="Filter by git branch"),
    is_git_repo: Optional[bool] = Query(None, description="Filter by git repository status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """List environment exports with optional filtering"""
    try:
        # Build query
        query = select(EnvExport).join(Project)
        conditions = []
        
        if project_id:
            conditions.append(EnvExport.project_id == project_id)
        if git_branch:
            conditions.append(EnvExport.git_branch == git_branch)
        if is_git_repo is not None:
            conditions.append(EnvExport.is_git_repo == is_git_repo)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(EnvExport)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = await db.execute(count_query)
        total = len(total_result.scalars().all())
        
        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(EnvExport.exported_at.desc())
        result = await db.execute(query)
        exports = result.scalars().all()
        
        return ExportListResponse(
            exports=[ExportResponse.model_validate(export) for export in exports],
            total=total,
            page=skip // limit + 1,
            size=limit
        )
        
    except Exception as e:
        logger.error(f"Error listing exports: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=ExportResponse)
async def create_export(
    export: ExportCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new export record"""
    try:
        # Check if project exists
        project_result = await db.execute(
            select(Project).where(Project.id == export.project_id)
        )
        project = project_result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Create the export
        db_export = EnvExport(**export.model_dump())
        db.add(db_export)
        await db.commit()
        await db.refresh(db_export)
        
        logger.info(f"Created export record: {db_export.export_path} for project: {project.name}")
        return ExportResponse.model_validate(db_export)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating export: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/check-updates", response_model=CheckUpdatesResponse)
async def check_updates(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    db: AsyncSession = Depends(get_db)
):
    """Check for outdated exports"""
    try:
        # Get all exports
        query = select(EnvExport)
        if project_id:
            query = query.where(EnvExport.project_id == project_id)
        
        result = await db.execute(query)
        exports = result.scalars().all()
        
        outdated_exports = []
        
        for export in exports:
            # For now, just check if the export exists and return basic info
            # TODO: Implement proper hash comparison
            outdated_exports.append({
                "export_id": export.id,
                "project_id": export.project_id,
                "export_path": export.export_path,
                "exported_at": export.exported_at,
                "is_outdated": False  # For now, assume not outdated
            })
        
        return CheckUpdatesResponse(
            outdated_exports=outdated_exports,
            total_checked=len(exports),
            outdated_count=len([e for e in outdated_exports if e["is_outdated"]])
        )
        
    except Exception as e:
        logger.error(f"Error checking updates: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{export_id}")
async def delete_export(
    export_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete an export record"""
    try:
        # Check if export exists
        result = await db.execute(
            select(EnvExport).where(EnvExport.id == export_id)
        )
        export = result.scalar_one_or_none()
        
        if not export:
            raise HTTPException(status_code=404, detail="Export not found")
        
        # Delete the export
        await db.delete(export)
        await db.commit()
        
        logger.info(f"Deleted export record: {export.export_path}")
        return {"message": f"Export {export_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting export: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{export_id}", response_model=ExportResponse)
async def get_export(
    export_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific export by ID"""
    try:
        result = await db.execute(
            select(EnvExport).where(EnvExport.id == export_id)
        )
        export = result.scalar_one_or_none()
        
        if not export:
            raise HTTPException(status_code=404, detail="Export not found")
        
        return ExportResponse.model_validate(export)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting export: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{export_id}", response_model=ExportResponse)
async def update_export(
    export_id: int,
    export_update: ExportUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an export record"""
    try:
        # Get existing export
        result = await db.execute(
            select(EnvExport).where(EnvExport.id == export_id)
        )
        db_export = result.scalar_one_or_none()
        
        if not db_export:
            raise HTTPException(status_code=404, detail="Export not found")
        
        # Update fields
        update_data = export_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_export, field, value)
        
        await db.commit()
        await db.refresh(db_export)
        
        logger.info(f"Updated export: {db_export.export_path}")
        return ExportResponse.model_validate(db_export)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating export: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{export_id}")
async def delete_export(
    export_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete an export record"""
    try:
        # Get existing export
        result = await db.execute(
            select(EnvExport).where(EnvExport.id == export_id)
        )
        db_export = result.scalar_one_or_none()
        
        if not db_export:
            raise HTTPException(status_code=404, detail="Export not found")
        
        # Delete the export
        await db.delete(db_export)
        await db.commit()
        
        logger.info(f"Deleted export: {db_export.export_path}")
        return {"message": "Export deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting export: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/export", response_model=ExportResult)
async def export_project(
    request: ExportRequest,
    db: AsyncSession = Depends(get_db)
):
    """Export project variables to .env file"""
    try:
        # Check if project exists by name
        project_result = await db.execute(
            select(Project).where(Project.name == request.project_name)
        )
        project = project_result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Resolve all variables for the project
        resolver = VariableResolver(db)
        resolved_values = await resolver.resolve_project_variables(project.id)
        
        if not resolved_values:
            raise HTTPException(
                status_code=400,
                detail="No variables found for this project"
            )
        
        # Apply prefix/suffix if specified
        final_values = {}
        for name, value in resolved_values.items():
            final_name = name
            final_value = value
            
            if request.with_prefix and request.prefix_value:
                final_name = f"{request.prefix_value}{name}"
            
            if request.with_suffix and request.suffix_value:
                final_name = f"{name}{request.suffix_value}"
            
            final_values[final_name] = final_value
        
        # Generate .env content
        env_content = ""
        for name, value in final_values.items():
            env_content += f"{name}={value}\n"
        
        # Calculate hash of resolved values
        values_hash = hashlib.sha256(
            json.dumps(final_values, sort_keys=True).encode()
        ).hexdigest()
        
        # Create export path
        from pathlib import Path
        export_path = str(Path(request.out_dir).resolve() / ".env")
        
        # Get git information
        git_info = get_git_info(export_path)
        
        # Create export record
        export_record = EnvExport(
            project_id=project.id,
            export_path=export_path,
            exported_at=datetime.utcnow(),
            with_prefix=request.with_prefix,
            with_suffix=request.with_suffix,
            prefix_value=request.prefix_value,
            suffix_value=request.suffix_value,
            resolved_values=final_values,
            export_hash=values_hash,
            git_repo_path=git_info["git_repo_path"],
            git_branch=git_info["git_branch"],
            git_commit_hash=git_info["git_commit_hash"],
            git_remote_url=git_info["git_remote_url"],
            is_git_repo=git_info["is_git_repo"]
        )
        
        db.add(export_record)
        await db.commit()
        await db.refresh(export_record)
        
        logger.info(f"Exported project '{project.name}' to {export_path}")
        
        return ExportResult(
            success=True,
            export_id=export_record.id,
            export_path=export_path,
            variables_exported=len(final_values),
            message=f"Successfully exported {len(final_values)} variables to {export_path}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting project: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")





@router.post("/diff", response_model=DiffResponse)
async def get_export_diff(
    request: DiffRequest,
    db: AsyncSession = Depends(get_db)
):
    """Get diff between stored export and current values"""
    try:
        # Get the export record
        result = await db.execute(
            select(EnvExport).where(EnvExport.id == request.export_id)
        )
        export = result.scalar_one_or_none()
        
        if not export:
            raise HTTPException(status_code=404, detail="Export not found")
        
        # Resolve current values
        resolver = VariableResolver(db)
        current_values = await resolver.resolve_project_variables(export.project_id)
        
        # Apply prefix/suffix to current values
        final_current_values = {}
        for name, value in current_values.items():
            final_name = name
            if export.with_prefix and export.prefix_value:
                final_name = f"{export.prefix_value}{name}"
            if export.with_suffix and export.suffix_value:
                final_name = f"{name}{export.suffix_value}"
            final_current_values[final_name] = value
        
        # Get stored values
        stored_values = export.resolved_values or {}
        
        # Calculate differences
        all_keys = set(final_current_values.keys()) | set(stored_values.keys())
        differences = []
        
        for key in all_keys:
            current_val = final_current_values.get(key)
            stored_val = stored_values.get(key)
            
            if current_val != stored_val:
                differences.append({
                    "variable": key,
                    "stored_value": stored_val,
                    "current_value": current_val,
                    "status": "modified" if stored_val is not None and current_val is not None else "added" if stored_val is None else "removed"
                })
        
        return DiffResponse(
            export_id=request.export_id,
            export_path=export.export_path,
            exported_at=export.exported_at,
            differences=differences,
            total_differences=len(differences)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting export diff: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 