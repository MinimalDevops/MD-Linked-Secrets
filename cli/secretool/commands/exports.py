"""
Exports management command for secretool CLI.
"""

import asyncio
from typing import Optional
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm

from ..api_client import APIClient
from ..config import CLIConfig


console = Console()


@click.command()
@click.option("--project", "-p", help="Filter by project name")
@click.option("--branch", "-b", help="Filter by git branch")
@click.option("--git-only", is_flag=True, help="Show only exports from git repositories")
@click.option("--limit", "-l", default=50, help="Maximum number of exports to show")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def list_exports(project: Optional[str], branch: Optional[str], git_only: bool, limit: int, verbose: bool):
    """List tracked exports with filtering options"""
    
    config = CLIConfig(verbose=verbose)
    
    async def run_list():
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
            
            # Get exports
            if verbose:
                console.print("🔍 Fetching exports...")
            exports_data = await client.list_exports(
                project_id=project_id,
                git_branch=branch,
                is_git_repo=git_only if git_only else None,
                limit=limit
            )
            
            exports = exports_data.get("exports", [])
            total = exports_data.get("total", 0)
            
            if not exports:
                console.print("[yellow]No exports found matching the criteria[/yellow]")
                return
            
            # Display exports
            table = Table(title=f"Tracked Exports ({len(exports)} of {total})")
            table.add_column("ID", style="cyan", width=6)
            table.add_column("Project", style="blue", width=15)
            table.add_column("Path", style="green", width=40)
            table.add_column("Branch", style="yellow", width=15)
            table.add_column("Exported", style="magenta", width=20)
            table.add_column("Git", style="red", width=8)
            
            for export in exports:
                git_status = "✅" if export.get("is_git_repo") else "❌"
                branch_name = export.get("git_branch", "N/A")
                exported_at = export.get("exported_at", "")
                if exported_at:
                    from datetime import datetime
                    try:
                        dt = datetime.fromisoformat(exported_at.replace('Z', '+00:00'))
                        exported_at = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        pass
                
                table.add_row(
                    str(export.get("id", "")),
                    export.get("project", {}).get("name", "Unknown"),
                    export.get("export_path", ""),
                    branch_name,
                    exported_at,
                    git_status
                )
            
            console.print(table)
            
            # Show summary
            git_count = sum(1 for e in exports if e.get("is_git_repo"))
            console.print(f"\n📊 Summary: {len(exports)} exports ({git_count} in git repos)")
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    asyncio.run(run_list())


@click.command()
@click.argument("export_id", type=int)
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def remove_export(export_id: int, force: bool, verbose: bool):
    """Remove an export from tracking"""
    
    config = CLIConfig(verbose=verbose)
    
    async def run_remove():
        try:
            client = APIClient(config)
            
            # Check API health
            if verbose:
                console.print("🔍 Checking API health...")
            await client.health_check()
            
            # Get export details first
            if verbose:
                console.print(f"🔍 Getting export details for ID: {export_id}")
            
            try:
                export_data = await client.get_export(export_id)
            except Exception as e:
                if "404" in str(e):
                    console.print(f"[red]Error: Export with ID {export_id} not found[/red]")
                    return
                raise
            
            # Show export details
            console.print(f"\n📄 Export Details:")
            console.print(f"   ID: {export_data.get('id')}")
            console.print(f"   Project: {export_data.get('project', {}).get('name', 'Unknown')}")
            console.print(f"   Path: {export_data.get('export_path')}")
            console.print(f"   Branch: {export_data.get('git_branch', 'N/A')}")
            console.print(f"   Exported: {export_data.get('exported_at')}")
            
            # Confirm deletion
            if not force:
                if not Confirm.ask(f"\n❓ Are you sure you want to remove this export from tracking?"):
                    console.print("❌ Operation cancelled")
                    return
            
            # Delete export
            if verbose:
                console.print(f"🗑️  Removing export {export_id}...")
            
            await client.delete_export(export_id)
            console.print(f"✅ Export {export_id} removed from tracking")
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    asyncio.run(run_remove())


@click.command()
@click.option("--project", "-p", help="Filter by project name")
@click.option("--branch", "-b", help="Filter by git branch")
@click.option("--git-only", is_flag=True, help="Show only exports from git repositories")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def export_summary(project: Optional[str], branch: Optional[str], git_only: bool, verbose: bool):
    """Show summary of tracked exports by project and branch"""
    
    config = CLIConfig(verbose=verbose)
    
    async def run_summary():
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
            
            # Get all exports
            if verbose:
                console.print("🔍 Fetching all exports...")
            exports_data = await client.list_exports(
                project_id=project_id,
                git_branch=branch,
                is_git_repo=git_only if git_only else None,
                limit=1000  # Get all exports for summary
            )
            
            exports = exports_data.get("exports", [])
            
            if not exports:
                console.print("[yellow]No exports found matching the criteria[/yellow]")
                return
            
            # Group by project and branch
            summary = {}
            for export in exports:
                project_name = export.get("project", {}).get("name", "Unknown")
                branch_name = export.get("git_branch") or "No Git"
                git_repo = export.get("is_git_repo", False)
                
                if project_name not in summary:
                    summary[project_name] = {}
                if branch_name not in summary[project_name]:
                    summary[project_name][branch_name] = {
                        "count": 0,
                        "git_repo": git_repo,
                        "exports": []
                    }
                
                summary[project_name][branch_name]["count"] += 1
                summary[project_name][branch_name]["exports"].append(export)
            
            # Display summary
            console.print(Panel("📊 Export Summary", style="bold blue"))
            
            for project_name, branches in summary.items():
                console.print(f"\n[bold cyan]📁 {project_name}[/bold cyan]")
                
                for branch_name, data in branches.items():
                    git_icon = "🌿" if data["git_repo"] else "📁"
                    console.print(f"  {git_icon} {branch_name}: {data['count']} exports")
                    
                    # Show export paths
                    for export in data["exports"][:3]:  # Show first 3
                        path = export.get("export_path", "")
                        console.print(f"    • {path}")
                    
                    if len(data["exports"]) > 3:
                        console.print(f"    • ... and {len(data['exports']) - 3} more")
            
            # Show totals
            total_exports = sum(sum(b["count"] for b in branches.values()) for branches in summary.values())
            git_exports = sum(
                sum(b["count"] for b in branches.values() if b["git_repo"]) 
                for branches in summary.values()
            )
            
            console.print(f"\n📈 Total: {total_exports} exports ({git_exports} in git repos)")
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    asyncio.run(run_summary())
