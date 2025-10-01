"""
Check-updates command for secretool CLI.
"""

import asyncio
from typing import Optional
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from datetime import datetime

from ..api_client import APIClient
from ..config import CLIConfig


console = Console()


@click.command()
@click.option("--project", "-p", help="Check updates for specific project only")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--suggest-commands", is_flag=True, default=True, help="Suggest re-export commands")
def check_updates(project: Optional[str], verbose: bool, suggest_commands: bool):
    """Check for outdated exports and suggest re-export commands"""
    
    config = CLIConfig(verbose=verbose)
    
    async def run_check():
        try:
            client = APIClient(config)
            
            # Check API health
            if verbose:
                console.print("🔍 Checking API health...")
            await client.health_check()
            
            # Get project ID if specified
            project_id = None
            if project:
                if verbose:
                    console.print(f"🔍 Looking up project: {project}")
                project_data = await client.get_project_by_name(project)
                if not project_data:
                    console.print(f"[red]Error: Project '{project}' not found[/red]")
                    return
                project_id = project_data["id"]
                if verbose:
                    console.print(f"✅ Found project: {project} (ID: {project_id})")
            
            # Check for updates
            if verbose:
                console.print("🔍 Checking for outdated exports...")
            updates_result = await client.check_updates(project_id=project_id)
            
            total_checked = updates_result.get("total_checked", 0)
            outdated_count = updates_result.get("outdated_count", 0)
            outdated_exports = updates_result.get("outdated_exports", [])
            
            # Display summary
            if outdated_count == 0:
                console.print(f"✅ All exports are up to date! (Checked {total_checked} exports)")
                return
            
            console.print(f"⚠️  Found {outdated_count} outdated exports out of {total_checked} total")
            
            # Display outdated exports
            table = Table(title="Outdated Exports")
            table.add_column("Export ID", style="cyan")
            table.add_column("Project", style="blue")
            table.add_column("Path", style="green")
            table.add_column("Exported At", style="yellow")
            table.add_column("Status", style="red")
            
            for export in outdated_exports:
                # Get project name
                project_name = "Unknown"
                if not project_id:
                    try:
                        project_data = await client.get_project_by_name("")  # This won't work, need to get by ID
                        # For now, just show the project ID
                        project_name = f"Project {export.get('project_id', 'Unknown')}"
                    except:
                        project_name = f"Project {export.get('project_id', 'Unknown')}"
                else:
                    project_name = project
                
                exported_at = export.get("exported_at", "")
                if exported_at:
                    try:
                        dt = datetime.fromisoformat(exported_at.replace('Z', '+00:00'))
                        exported_at = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        pass
                
                table.add_row(
                    str(export.get("export_id", "N/A")),
                    project_name,
                    export.get("export_path", "N/A"),
                    exported_at,
                    "Outdated"
                )
            
            console.print(table)
            
            # Suggest re-export commands
            if suggest_commands and outdated_exports:
                console.print("\n[bold]Suggested re-export commands:[/bold]")
                
                for export in outdated_exports:
                    export_path = export.get("export_path", "")
                    if export_path:
                        # Extract project name from path or use project parameter
                        project_name = project if project else f"Project {export.get('project_id', 'Unknown')}"
                        
                        # Build the command
                        cmd = f"secretool export --project {project_name} --out-dir {export_path}"
                        
                        # Add prefix/suffix if they were used
                        if export.get("with_prefix") and export.get("prefix_value"):
                            cmd += f" --prefix {export.get('prefix_value')}"
                        if export.get("with_suffix") and export.get("suffix_value"):
                            cmd += f" --suffix {export.get('suffix_value')}"
                        
                        console.print(f"  [cyan]{cmd}[/cyan]")
                
                console.print(f"\n[dim]Or run: secretool export --project {project or 'PROJECT_NAME'} to re-export all[/dim]")
        
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            if verbose:
                import traceback
                console.print(traceback.format_exc())
    
    asyncio.run(run_check()) 