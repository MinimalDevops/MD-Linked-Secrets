"""
API client for communicating with the MD-Linked-Secrets backend.
"""

import httpx
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

from .config import CLIConfig


class APIClient:
    """Client for communicating with the MD-Linked-Secrets API"""
    
    def __init__(self, config: CLIConfig):
        self.config = config
        self.base_url = config.api_base_url.rstrip('/')
        self.timeout = config.api_timeout
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to the API"""
        
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, params=params)
                elif method.upper() == "POST":
                    response = await client.post(url, json=data)
                elif method.upper() == "PUT":
                    response = await client.put(url, json=data)
                elif method.upper() == "DELETE":
                    response = await client.delete(url)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                error_detail = e.response.json().get('detail', 'Unknown error') if e.response.content else 'Unknown error'
                raise Exception(f"API Error ({e.response.status_code}): {error_detail}")
            except httpx.RequestError as e:
                raise Exception(f"Network Error: {e}")
    
    async def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects"""
        response = await self._make_request("GET", "/api/v1/projects/")
        return response.get("projects", [])
    
    async def get_project_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a project by name"""
        projects = await self.get_projects()
        for project in projects:
            if project["name"] == name:
                return project
        return None
    
    async def get_env_vars(self, project_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get environment variables, optionally filtered by project"""
        params = {"project_id": project_id} if project_id else None
        response = await self._make_request("GET", "/api/v1/env-vars/", params=params)
        return response.get("variables", [])
    
    async def resolve_variables(self, project_id: Optional[int] = None, var_id: Optional[int] = None) -> Dict[str, str]:
        """Resolve variables for a project or specific variable"""
        data = {}
        if project_id:
            data["project_id"] = project_id
        elif var_id:
            data["var_id"] = var_id
        else:
            raise ValueError("Either project_id or var_id must be provided")
        
        response = await self._make_request("POST", "/api/v1/env-vars/resolve", data=data)
        return response.get("resolved_values", {})
    
    async def export_project(
        self, 
        project_id: int, 
        export_path: str,
        with_prefix: bool = False,
        with_suffix: bool = False,
        prefix_value: Optional[str] = None,
        suffix_value: Optional[str] = None
    ) -> Dict[str, Any]:
        """Export project variables to a .env file"""
        
        # Get project name from project_id
        projects = await self.get_projects()
        project_name = None
        for project in projects:
            if project["id"] == project_id:
                project_name = project["name"]
                break
        
        if not project_name:
            raise ValueError(f"Project with ID {project_id} not found")
        
        # Extract out_dir from export_path
        from pathlib import Path
        out_dir = str(Path(export_path).parent)
        
        data = {
            "project_name": project_name,
            "out_dir": out_dir,
            "with_prefix": with_prefix,
            "with_suffix": with_suffix
        }
        
        if prefix_value:
            data["prefix_value"] = prefix_value
        if suffix_value:
            data["suffix_value"] = suffix_value
        
        return await self._make_request("POST", "/api/v1/exports/export", data=data)
    
    async def check_updates(self, project_id: Optional[int] = None) -> Dict[str, Any]:
        """Check for outdated exports"""
        params = {"project_id": project_id} if project_id else None
        return await self._make_request("GET", "/api/v1/exports/check-updates", params=params)
    
    async def get_export_diff(self, export_id: int) -> Dict[str, Any]:
        """Get diff between stored export and current values"""
        data = {"export_id": export_id}
        return await self._make_request("POST", "/api/v1/exports/diff", data=data)
    
    async def preview_env_import(self, import_request: Dict[str, Any]) -> Dict[str, Any]:
        """Preview what will be imported from .env content"""
        return await self._make_request("POST", "/api/v1/imports/preview", data=import_request)
    
    async def import_env_variables(self, import_request: Dict[str, Any]) -> Dict[str, Any]:
        """Import variables from .env content into a project"""
        return await self._make_request("POST", "/api/v1/imports/import", data=import_request)
    
    async def get_imports(self, project_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get import history, optionally filtered by project"""
        params = {"project_id": project_id} if project_id else None
        return await self._make_request("GET", "/api/v1/imports/", params=params)
    
    async def get_exports(self, project_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all exports, optionally filtered by project"""
        params = {"project_id": project_id} if project_id else None
        response = await self._make_request("GET", "/api/v1/exports/", params=params)
        return response.get("exports", [])
    
    async def list_exports(
        self, 
        project_id: Optional[int] = None,
        git_branch: Optional[str] = None,
        is_git_repo: Optional[bool] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """List exports with filtering options"""
        params = {
            "limit": limit
        }
        if project_id:
            params["project_id"] = project_id
        if git_branch:
            params["git_branch"] = git_branch
        if is_git_repo is not None:
            params["is_git_repo"] = is_git_repo
        
        return await self._make_request("GET", "/api/v1/exports/", params=params)
    
    async def get_export(self, export_id: int) -> Dict[str, Any]:
        """Get a specific export by ID"""
        return await self._make_request("GET", f"/api/v1/exports/{export_id}")
    
    async def delete_export(self, export_id: int) -> Dict[str, Any]:
        """Delete an export record"""
        return await self._make_request("DELETE", f"/api/v1/exports/{export_id}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        return await self._make_request("GET", "/health") 