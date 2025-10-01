from typing import Dict, List, Optional, Set, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models import EnvVar, Project, EnvExport
import logging
import re

logger = logging.getLogger(__name__)


class VariableResolver:
    """Core engine for resolving environment variables with linking and concatenation"""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self._cache: Dict[int, str] = {}  # Cache resolved values
        self._resolving: Set[int] = set()  # Track variables being resolved (for circular detection)
    
    async def resolve_variable(self, var_id: int) -> Optional[str]:
        """Resolve a single variable by ID"""
        if var_id in self._cache:
            return self._cache[var_id]
        
        if var_id in self._resolving:
            raise ValueError(f"Circular reference detected for variable ID {var_id}")
        
        # Get the variable
        result = await self.db_session.execute(
            select(EnvVar).where(EnvVar.id == var_id)
        )
        var = result.scalar_one_or_none()
        
        if not var:
            return None
        
        return await self._resolve_var_value(var)
    
    async def resolve_project_variables(self, project_id: int) -> Dict[str, str]:
        """Resolve all variables for a project"""
        result = await self.db_session.execute(
            select(EnvVar).where(EnvVar.project_id == project_id)
        )
        variables = result.scalars().all()
        
        resolved = {}
        for var in variables:
            try:
                value = await self._resolve_var_value(var)
                if value is not None:
                    resolved[var.name] = value
            except Exception as e:
                logger.error(f"Failed to resolve variable {var.name}: {e}")
                # Continue with other variables
        
        return resolved
    
    async def _resolve_var_value(self, var: EnvVar) -> Optional[str]:
        """Resolve the value of a single variable"""
        if var.id in self._cache:
            return self._cache[var.id]
        
        if var.id in self._resolving:
            raise ValueError(f"Circular reference detected for variable {var.name}")
        
        self._resolving.add(var.id)
        
        try:
            if var.raw_value is not None:
                resolved_value = var.raw_value
            elif var.linked_to is not None:
                resolved_value = await self._resolve_linked_variable(var.linked_to)
            elif var.concat_parts is not None:
                resolved_value = await self._resolve_concatenated_variable(var.concat_parts)
            else:
                resolved_value = None
            
            # Cache the result
            if resolved_value is not None:
                self._cache[var.id] = resolved_value
            
            return resolved_value
            
        finally:
            self._resolving.remove(var.id)
    
    async def _resolve_linked_variable(self, linked_to: str) -> Optional[str]:
        """Resolve a linked variable (PROJECT:VAR format)"""
        if not self._is_valid_linked_format(linked_to):
            raise ValueError(f"Invalid linked variable format: {linked_to}")
        
        project_name, var_name = linked_to.split(':', 1)
        
        # Find the target variable
        result = await self.db_session.execute(
            select(EnvVar)
            .join(Project)
            .where(Project.name == project_name, EnvVar.name == var_name)
        )
        target_var = result.scalar_one_or_none()
        
        if not target_var:
            raise ValueError(f"Linked variable not found: {linked_to}")
        
        return await self._resolve_var_value(target_var)
    
    async def _resolve_concatenated_variable(self, concat_parts: str) -> Optional[str]:
        """Resolve a concatenated variable (PROJECT:VAR with optional separators)"""
        # Extract PROJECT:VAR parts using regex - now supporting quoted format
        import re
        # Use quoted format: "PROJECT:VAR" separated by any character(s)
        # This allows variable names to contain any characters including separators
        
        # First try to find quoted PROJECT:VAR patterns and preserve separators
        quoted_matches = re.finditer(r'"([A-Za-z0-9_-]+:[A-Za-z0-9_-]+)"', concat_parts)
        
        if quoted_matches:
            # Use quoted format - reconstruct with separators
            result = concat_parts
            quoted_matches = re.finditer(r'"([A-Za-z0-9_-]+:[A-Za-z0-9_-]+)"', concat_parts)
            
            # Process matches in reverse order to avoid position shifts
            matches = list(quoted_matches)
            for match in reversed(matches):
                full_match = match.group(0)  # The full quoted string
                var_reference = match.group(1)  # The PROJECT:VAR part
                
                # Resolve the variable
                project_name, var_name = var_reference.split(':', 1)
                
                # Find the project
                from app.models.project import Project
                project_result = await self.db_session.execute(
                    select(Project).where(Project.name == project_name)
                )
                target_project = project_result.scalar_one_or_none()
                
                if not target_project:
                    raise ValueError(f"Project not found: {project_name}")
                
                # Find the variable in that project
                var_result = await self.db_session.execute(
                    select(EnvVar).where(
                        EnvVar.project_id == target_project.id,
                        EnvVar.name == var_name
                    )
                )
                target_var = var_result.scalar_one_or_none()
                
                if not target_var:
                    raise ValueError(f"Variable not found: {var_reference}")
                
                # Resolve the target variable's value recursively
                resolved_value = await self._resolve_var_value(target_var)
                if resolved_value is not None:
                    # Replace the quoted variable with its resolved value
                    result = result[:match.start()] + resolved_value + result[match.end():]
            
            return result
        else:
            # Fallback to old format for backward compatibility
            separators_pattern = r'[\|_\-/\\;, ]+'
            potential_parts = re.split(separators_pattern, concat_parts)
            parts = []
            
            for part in potential_parts:
                if part and re.match(r'^[A-Za-z0-9_-]+:[A-Za-z0-9_-]+$', part.strip()):
                    parts.append(part.strip())
            
            if not parts:
                return None
                
            resolved_parts = []
            
            for part in parts:
                # Each part is in format PROJECT:VAR - need to find the actual variable
                project_name, var_name = part.split(':', 1)
                
                # Find the project
                from app.models.project import Project
                project_result = await self.db_session.execute(
                    select(Project).where(Project.name == project_name)
                )
                target_project = project_result.scalar_one_or_none()
                
                if not target_project:
                    raise ValueError(f"Project not found: {project_name}")
                
                # Find the variable in that project
                var_result = await self.db_session.execute(
                    select(EnvVar).where(
                        EnvVar.project_id == target_project.id,
                        EnvVar.name == var_name
                    )
                )
                target_var = var_result.scalar_one_or_none()
                
                if not target_var:
                    raise ValueError(f"Variable not found: {part}")
                
                # Resolve the target variable's value recursively
                resolved_part = await self._resolve_var_value(target_var)
                if resolved_part is not None:
                    resolved_parts.append(resolved_part)
            
            return ''.join(resolved_parts) if resolved_parts else None
    
    def _is_valid_linked_format(self, linked_to: str) -> bool:
        """Validate linked variable format (PROJECT:VAR)"""
        pattern = r'^[A-Za-z0-9_-]+:[A-Za-z0-9_-]+$'
        return bool(re.match(pattern, linked_to))
    
    def _is_valid_concat_format(self, concat_parts: str) -> bool:
        """Validate concatenated variable format (PROJECT:VAR with optional separators)"""
        pattern = r'^[A-Za-z0-9_-]+:[A-Za-z0-9_-]+([^A-Za-z0-9_-]*[A-Za-z0-9_-]+:[A-Za-z0-9_-]+)*$'
        return bool(re.match(pattern, concat_parts))
    
    async def get_affected_exports(self, var_id: int) -> List[Dict]:
        """Get all exports that would be affected by a change to this variable"""
        # First, get the source variable
        result = await self.db_session.execute(
            select(EnvVar).where(EnvVar.id == var_id)
        )
        source_var = result.scalar_one_or_none()
        
        if not source_var:
            return []
        
        # Get all variables that depend on this one (directly or indirectly)
        dependent_vars = await self._get_dependent_variables(var_id)
        
        # Include the source variable itself in the list
        all_affected_vars = [source_var] + dependent_vars
        
        # Get all exports that contain any of these variables
        affected_exports = []
        seen_exports = set()  # To avoid duplicates
        
        for var in all_affected_vars:
            result = await self.db_session.execute(
                select(EnvExport).where(EnvExport.project_id == var.project_id)
            )
            exports = result.scalars().all()
            
            for export in exports:
                if export.resolved_values and var.name in export.resolved_values:
                    # Avoid duplicates
                    export_key = f"{export.id}_{var.name}"
                    if export_key not in seen_exports:
                        seen_exports.add(export_key)
                        affected_exports.append({
                            "export_id": export.id,
                            "project_id": export.project_id,
                            "export_path": export.export_path,
                            "exported_at": export.exported_at,
                            "affected_variable": var.name,
                            "git_repo_path": export.git_repo_path,
                            "git_branch": export.git_branch,
                            "git_commit_hash": export.git_commit_hash,
                            "git_remote_url": export.git_remote_url,
                            "is_git_repo": export.is_git_repo
                        })
        
        return affected_exports
    
    async def _get_dependent_variables(self, var_id: int) -> List[EnvVar]:
        """Get all variables that depend on the given variable (directly or indirectly)"""
        # First, get the variable we're checking dependencies for
        result = await self.db_session.execute(
            select(EnvVar).where(EnvVar.id == var_id)
        )
        target_var = result.scalar_one_or_none()
        
        if not target_var:
            return []
        
        # Get the project name and variable name
        project_result = await self.db_session.execute(
            select(Project).where(Project.id == target_var.project_id)
        )
        project = project_result.scalar_one_or_none()
        
        if not project:
            return []
        
        # Build the reference string that other variables would use
        reference_string = f"{project.name}:{target_var.name}"
        
        # Find variables that actually reference this specific variable
        dependent_vars = []
        
        # Check linked_to references
        linked_result = await self.db_session.execute(
            select(EnvVar).where(EnvVar.linked_to == reference_string)
        )
        dependent_vars.extend(linked_result.scalars().all())
        
        # Check concat_parts references
        concat_result = await self.db_session.execute(
            select(EnvVar).where(EnvVar.concat_parts.contains(reference_string))
        )
        dependent_vars.extend(concat_result.scalars().all())
        
        return dependent_vars
    
    def clear_cache(self):
        """Clear the resolution cache"""
        self._cache.clear()
        self._resolving.clear()
    
    async def validate_variable_references(self, var) -> List[str]:
        """Validate that all referenced variables exist"""
        errors = []
        
        if hasattr(var, 'linked_to') and var.linked_to:
            if not await self._validate_linked_reference(var.linked_to):
                errors.append(f"Linked variable not found: {var.linked_to}")
        
        if hasattr(var, 'concat_parts') and var.concat_parts:
            # Extract PROJECT:VAR parts using regex - now supporting quoted format
            import re
            # Use quoted format: "PROJECT:VAR" separated by any character(s)
            # This allows variable names to contain any characters including separators
            
            # First try to find quoted PROJECT:VAR patterns
            quoted_parts = re.findall(r'"([A-Za-z0-9_-]+:[A-Za-z0-9_-]+)"', var.concat_parts)
            
            if quoted_parts:
                # Use quoted format
                parts = quoted_parts
            else:
                # Fallback to old format for backward compatibility
                separators_pattern = r'[\|_\-/\\;, ]+'
                potential_parts = re.split(separators_pattern, var.concat_parts)
                parts = []
                
                for part in potential_parts:
                    if part and re.match(r'^[A-Za-z0-9_-]+:[A-Za-z0-9_]+$', part.strip()):
                        parts.append(part.strip())
            for part in parts:
                if not await self._validate_linked_reference(part):
                    errors.append(f"Concatenated variable part not found: {part}")
        
        return errors
    
    async def _validate_linked_reference(self, linked_to: str) -> bool:
        """Check if a linked variable reference is valid"""
        if not self._is_valid_linked_format(linked_to):
            return False
        
        project_name, var_name = linked_to.split(':', 1)
        
        result = await self.db_session.execute(
            select(EnvVar)
            .join(Project)
            .where(Project.name == project_name, EnvVar.name == var_name)
        )
        
        return result.scalar_one_or_none() is not None 