from typing import List, Dict, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import re
import hashlib
from datetime import datetime

from ..models import Project, EnvVar, EnvImport
from ..schemas.import_schemas import (
    EnvFileImportRequest, ParsedEnvVariable, ImportConflict, 
    EnvImportPreview, EnvImportResult
)
from ..schemas.env_var import EnvVarCreate
from .variable_history_service import VariableHistoryService


class EnvImportService:
    """Service for parsing and importing .env files"""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    def parse_env_content(self, content: str) -> Tuple[List[ParsedEnvVariable], List[str], List[str]]:
        """Parse .env file content into variables"""
        variables = []
        skipped_lines = []
        warnings = []
        
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                if line:  # Only track non-empty skipped lines
                    skipped_lines.append(f"Line {line_num}: {line} (comment)")
                continue
            
            # Check for variable assignment
            if '=' not in line:
                skipped_lines.append(f"Line {line_num}: {line} (no assignment)")
                warnings.append(f"Line {line_num}: No '=' found, skipping")
                continue
            
            # Split on first '=' to handle values with '=' in them
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            # Remove inline comments (everything after # in the value)
            if '#' in value:
                comment_start = value.find('#')
                # Check if the # is inside quotes
                quote_start = value.find('"')
                single_quote_start = value.find("'")
                
                # If # is not inside quotes, remove the comment
                if (quote_start == -1 or comment_start < quote_start) and \
                   (single_quote_start == -1 or comment_start < single_quote_start):
                    value = value[:comment_start].strip()
            
            # Remove quotes from value if present
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            
            # Validate variable name
            if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', key):
                warnings.append(f"Line {line_num}: Invalid variable name '{key}', but importing anyway")
            
            variables.append(ParsedEnvVariable(
                name=key,
                value=value,
                original_name=key,
                line_number=line_num
            ))
        
        return variables, skipped_lines, warnings
    
    def apply_transformations(self, variables: List[ParsedEnvVariable], request: EnvFileImportRequest) -> List[ParsedEnvVariable]:
        """Apply prefix/suffix transformations to variable names"""
        transformed = []
        
        for var in variables:
            new_name = var.name
            
            # Strip prefix
            if request.strip_prefix and new_name.startswith(request.strip_prefix):
                new_name = new_name[len(request.strip_prefix):]
            
            # Strip suffix
            if request.strip_suffix and new_name.endswith(request.strip_suffix):
                new_name = new_name[:-len(request.strip_suffix)]
            
            # Add prefix
            if request.add_prefix:
                new_name = f"{request.add_prefix}{new_name}"
            
            # Add suffix
            if request.add_suffix:
                new_name = f"{new_name}{request.add_suffix}"
            
            transformed.append(ParsedEnvVariable(
                name=new_name,
                value=var.value,
                original_name=var.original_name,
                line_number=var.line_number
            ))
        
        return transformed
    
    async def check_conflicts(self, variables: List[ParsedEnvVariable], project_id: int) -> List[ImportConflict]:
        """Check for conflicts with existing variables"""
        conflicts = []
        
        # Get all existing variables for the project
        result = await self.db_session.execute(
            select(EnvVar).where(EnvVar.project_id == project_id)
        )
        existing_vars = {var.name: var for var in result.scalars().all()}
        
        for var in variables:
            if var.name in existing_vars:
                existing_var = existing_vars[var.name]
                
                # Determine variable type
                if existing_var.raw_value:
                    var_type = 'raw'
                    existing_value = existing_var.raw_value
                elif existing_var.linked_to:
                    var_type = 'linked'
                    existing_value = existing_var.linked_to
                else:
                    var_type = 'concatenated'
                    existing_value = existing_var.concat_parts
                
                conflicts.append(ImportConflict(
                    variable_name=var.name,
                    existing_value=existing_value,
                    new_value=var.value,
                    existing_type=var_type,
                    action='skip'  # Default action
                ))
        
        return conflicts
    
    async def preview_import(self, request: EnvFileImportRequest) -> EnvImportPreview:
        """Preview what will be imported without actually importing"""
        # Parse content
        variables, skipped_lines, warnings = self.parse_env_content(request.env_content)
        
        # Apply transformations
        variables = self.apply_transformations(variables, request)
        
        # Check conflicts
        conflicts = await self.check_conflicts(variables, request.project_id)
        
        # Separate new variables from conflicts
        conflict_names = {c.variable_name for c in conflicts}
        new_variables = [v for v in variables if v.name not in conflict_names]
        
        return EnvImportPreview(
            total_variables=len(variables),
            new_variables=new_variables,
            conflicts=conflicts,
            skipped_lines=skipped_lines,
            warnings=warnings
        )
    
    async def import_variables(self, request: EnvFileImportRequest) -> EnvImportResult:
        """Import variables into the project"""
        errors = []
        warnings = []
        
        try:
            # Verify project exists
            project_result = await self.db_session.execute(
                select(Project).where(Project.id == request.project_id)
            )
            project = project_result.scalar_one_or_none()
            if not project:
                return EnvImportResult(
                    success=False,
                    import_id=None,
                    variables_imported=0,
                    variables_skipped=0,
                    variables_overwritten=0,
                    conflicts_resolved=0,
                    errors=["Project not found"],
                    warnings=[],
                    message="Import failed: Project not found"
                )
            
            # Parse and transform variables
            variables, skipped_lines, parse_warnings = self.parse_env_content(request.env_content)
            variables = self.apply_transformations(variables, request)
            warnings.extend(parse_warnings)
            
            # Check conflicts
            conflicts = await self.check_conflicts(variables, request.project_id)
            
            # Process imports
            variables_imported = 0
            variables_skipped = 0
            variables_overwritten = 0
            conflicts_resolved = 0
            
            conflict_names = {c.variable_name for c in conflicts}
            
            # Import new variables (no conflicts)
            for var in variables:
                if var.name not in conflict_names:
                    try:
                        # Create new environment variable
                        custom_description = request.description if request.description else f"Imported from .env file (line {var.line_number})"
                        env_var = EnvVar(
                            project_id=request.project_id,
                            name=var.name,
                            raw_value=var.value,
                            description=custom_description
                        )
                        self.db_session.add(env_var)
                        await self.db_session.flush()  # Get the ID
                        
                        # Create history entry
                        history_service = VariableHistoryService(self.db_session)
                        await history_service.create_history_entry(
                            env_var, 
                            "created", 
                            f"Variable imported from .env file (line {var.line_number})",
                            "import_service"
                        )
                        
                        variables_imported += 1
                    except Exception as e:
                        errors.append(f"Failed to import '{var.name}': {str(e)}")
                        variables_skipped += 1
            
            # Handle conflicts based on individual resolutions or global overwrite setting
            for conflict in conflicts:
                # Determine action for this specific conflict
                should_overwrite = False
                if request.conflict_resolutions and conflict.variable_name in request.conflict_resolutions:
                    # Use individual resolution
                    should_overwrite = request.conflict_resolutions[conflict.variable_name] == 'overwrite'
                else:
                    # Fall back to global setting
                    should_overwrite = request.overwrite_existing
                
                if should_overwrite:
                    try:
                        # Find and update existing variable
                        result = await self.db_session.execute(
                            select(EnvVar).where(
                                and_(
                                    EnvVar.project_id == request.project_id,
                                    EnvVar.name == conflict.variable_name
                                )
                            )
                        )
                        existing_var = result.scalar_one_or_none()
                        
                        if existing_var:
                            # Update to raw value (import always creates raw values)
                            existing_var.raw_value = conflict.new_value
                            existing_var.linked_to = None
                            existing_var.concat_parts = None
                            existing_var.description = f"Updated from .env import"
                            
                            # Create history entry for overwrite
                            history_service = VariableHistoryService(self.db_session)
                            await history_service.create_history_entry(
                                existing_var, 
                                "updated", 
                                f"Variable overwritten during .env import",
                                "import_service"
                            )
                            
                            variables_overwritten += 1
                            conflicts_resolved += 1
                    except Exception as e:
                        errors.append(f"Failed to overwrite '{conflict.variable_name}': {str(e)}")
                        variables_skipped += 1
                else:
                    variables_skipped += 1
            
            # Create import record
            import_hash = hashlib.sha256(request.env_content.encode()).hexdigest()
            
            env_import = EnvImport(
                project_id=request.project_id,
                import_source='api',  # Will be overridden by specific sources (cli, frontend)
                import_description=f"Imported {len(variables)} variables",
                variables_imported=variables_imported,
                variables_skipped=variables_skipped,
                variables_overwritten=variables_overwritten,
                import_hash=import_hash
            )
            
            self.db_session.add(env_import)
            await self.db_session.commit()
            await self.db_session.refresh(env_import)
            
            success = len(errors) == 0
            message = f"Successfully imported {variables_imported} variables"
            if variables_skipped > 0:
                message += f", skipped {variables_skipped}"
            if variables_overwritten > 0:
                message += f", overwritten {variables_overwritten}"
            
            return EnvImportResult(
                success=success,
                import_id=env_import.id,
                variables_imported=variables_imported,
                variables_skipped=variables_skipped,
                variables_overwritten=variables_overwritten,
                conflicts_resolved=conflicts_resolved,
                errors=errors,
                warnings=warnings,
                message=message
            )
            
        except Exception as e:
            await self.db_session.rollback()
            return EnvImportResult(
                success=False,
                import_id=None,
                variables_imported=0,
                variables_skipped=0,
                variables_overwritten=0,
                conflicts_resolved=0,
                errors=[f"Import failed: {str(e)}"],
                warnings=warnings,
                message="Import operation failed"
            ) 