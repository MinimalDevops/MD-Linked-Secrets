from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from sqlalchemy.orm import selectinload
import hashlib
from datetime import datetime

from ..models import VariableHistory, EnvVar, Project
from ..schemas.variable_history import VariableHistoryCreate, VariableHistoryResponse


class VariableHistoryService:
    """Service for managing variable history and versioning"""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    async def create_history_entry(
        self, 
        env_var: EnvVar, 
        change_type: str, 
        change_reason: str = None,
        changed_by: str = None
    ) -> VariableHistory:
        """Create a new history entry for a variable"""
        
        # Get the next version number
        next_version = await self._get_next_version_number(env_var.id)
        
        # Create history entry
        history_entry = VariableHistory(
            env_var_id=env_var.id,
            project_id=env_var.project_id,
            version_number=next_version,
            variable_name=env_var.name,
            raw_value=env_var.raw_value,
            linked_to=env_var.linked_to,
            concat_parts=env_var.concat_parts,
            description=env_var.description,
            is_encrypted=env_var.is_encrypted,
            change_type=change_type,
            change_reason=change_reason or f"Variable {change_type}",
            changed_by=changed_by
        )
        
        self.db_session.add(history_entry)
        
        # Clean up old history if needed
        await self._cleanup_old_history(env_var.id, env_var.project_id)
        
        return history_entry
    
    async def get_variable_history(
        self, 
        env_var_id: int, 
        limit: Optional[int] = None
    ) -> List[VariableHistory]:
        """Get history for a specific variable"""
        
        query = select(VariableHistory).where(
            VariableHistory.env_var_id == env_var_id
        ).order_by(desc(VariableHistory.version_number))
        
        if limit:
            query = query.limit(limit)
        
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    async def get_project_history(
        self, 
        project_id: int, 
        limit: Optional[int] = None
    ) -> List[VariableHistory]:
        """Get all history for a project"""
        
        query = select(VariableHistory).where(
            VariableHistory.project_id == project_id
        ).order_by(desc(VariableHistory.created_at))
        
        if limit:
            query = query.limit(limit)
        
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    async def restore_variable_version(
        self, 
        env_var_id: int, 
        version_number: int,
        change_reason: str = None,
        changed_by: str = None
    ) -> bool:
        """Restore a variable to a specific version"""
        
        # Get the target version
        history_result = await self.db_session.execute(
            select(VariableHistory).where(
                and_(
                    VariableHistory.env_var_id == env_var_id,
                    VariableHistory.version_number == version_number
                )
            )
        )
        target_version = history_result.scalar_one_or_none()
        
        if not target_version:
            return False
        
        # Get the current variable
        var_result = await self.db_session.execute(
            select(EnvVar).where(EnvVar.id == env_var_id)
        )
        current_var = var_result.scalar_one_or_none()
        
        if not current_var:
            return False
        
        # Create history entry for current state before restoration
        await self.create_history_entry(
            current_var, 
            "updated",
            f"Before restoration to version {version_number}",
            changed_by
        )
        
        # Restore the variable
        current_var.raw_value = target_version.raw_value
        current_var.linked_to = target_version.linked_to
        current_var.concat_parts = target_version.concat_parts
        current_var.description = target_version.description
        current_var.is_encrypted = target_version.is_encrypted
        
        # Create history entry for the restoration
        await self.create_history_entry(
            current_var,
            "restored",
            change_reason or f"Restored to version {version_number}",
            changed_by
        )
        
        return True
    
    async def update_project_history_settings(
        self, 
        project_id: int, 
        history_limit: int,
        confirm_cleanup: bool = False
    ) -> Dict[str, Any]:
        """Update project history settings"""
        
        # Get current project settings
        project_result = await self.db_session.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project_result.scalar_one_or_none()
        
        if not project:
            return {"success": False, "error": "Project not found"}
        
        old_limit = project.history_limit
        new_limit = history_limit
        
        # Check if we need to warn about cleanup
        if new_limit < old_limit:
            # Count variables that would lose history
            affected_vars_result = await self.db_session.execute(
                select(
                    VariableHistory.env_var_id,
                    func.count(VariableHistory.id).label('history_count')
                ).where(
                    VariableHistory.project_id == project_id
                ).group_by(
                    VariableHistory.env_var_id
                ).having(
                    func.count(VariableHistory.id) > new_limit
                )
            )
            affected_vars = affected_vars_result.all()
            
            if affected_vars and not confirm_cleanup:
                total_entries_to_remove = sum(
                    var.history_count - new_limit for var in affected_vars
                )
                
                return {
                    "success": False,
                    "requires_confirmation": True,
                    "warning": f"Reducing history limit from {old_limit} to {new_limit} will remove {total_entries_to_remove} history entries from {len(affected_vars)} variables. This action cannot be undone.",
                    "affected_variables": len(affected_vars),
                    "entries_to_remove": total_entries_to_remove
                }
        
        # Update the project settings
        project.history_limit = new_limit
        
        # Clean up excess history if reducing limit
        if new_limit < old_limit:
            await self._cleanup_all_project_history(project_id, new_limit)
        
        await self.db_session.commit()
        
        return {
            "success": True,
            "old_limit": old_limit,
            "new_limit": new_limit,
            "message": f"History limit updated from {old_limit} to {new_limit}"
        }
    
    async def _get_next_version_number(self, env_var_id: int) -> int:
        """Get the next version number for a variable"""
        
        result = await self.db_session.execute(
            select(func.max(VariableHistory.version_number)).where(
                VariableHistory.env_var_id == env_var_id
            )
        )
        max_version = result.scalar()
        return (max_version or 0) + 1
    
    async def _cleanup_old_history(self, env_var_id: int, project_id: int):
        """Clean up old history entries based on project settings"""
        
        # Get project history limit
        project_result = await self.db_session.execute(
            select(Project.history_limit).where(Project.id == project_id)
        )
        history_limit = project_result.scalar() or 5
        
        # Get entries to delete (keep only the most recent ones)
        entries_to_delete = await self.db_session.execute(
            select(VariableHistory).where(
                VariableHistory.env_var_id == env_var_id
            ).order_by(desc(VariableHistory.version_number)).offset(history_limit)
        )
        
        for entry in entries_to_delete.scalars():
            await self.db_session.delete(entry)
    
    async def _cleanup_all_project_history(self, project_id: int, new_limit: int):
        """Clean up history for all variables in a project"""
        
        # Get all variables in the project
        vars_result = await self.db_session.execute(
            select(EnvVar.id).where(EnvVar.project_id == project_id)
        )
        
        for var_id_tuple in vars_result.all():
            var_id = var_id_tuple[0]
            
            # Delete excess history for this variable
            entries_to_delete = await self.db_session.execute(
                select(VariableHistory).where(
                    VariableHistory.env_var_id == var_id
                ).order_by(desc(VariableHistory.version_number)).offset(new_limit)
            )
            
            for entry in entries_to_delete.scalars():
                await self.db_session.delete(entry)
    
    async def get_variable_with_history(self, env_var_id: int) -> Optional[Dict[str, Any]]:
        """Get a variable with its complete history"""
        
        # Get the current variable
        var_result = await self.db_session.execute(
            select(EnvVar).options(selectinload(EnvVar.history)).where(
                EnvVar.id == env_var_id
            )
        )
        variable = var_result.scalar_one_or_none()
        
        if not variable:
            return None
        
        return {
            "current": variable.to_dict(),
            "history": [h.to_dict() for h in variable.history]
        } 