"""
Import command for secretool CLI.
"""

import asyncio
from pathlib import Path
from typing import Optional
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..api_client import APIClient
from ..config import CLIConfig


console = Console()


@click.command()
@click.option("--project", "-p", help="Project name to import into")
@click.option("--env-file", "-f", required=True, help="Path to .env file to import")
@click.option("--overwrite", is_flag=True, help="Overwrite existing variables")
@click.option("--strip-prefix", help="Prefix to strip from variable names")
@click.option("--strip-suffix", help="Suffix to strip from variable names")
@click.option("--add-prefix", help="Prefix to add to variable names")
@click.option("--add-suffix", help="Suffix to add to variable names")
@click.option("--description", help="Custom description for imported variables")
@click.option("--preview", is_flag=True, help="Preview what would be imported without actually importing")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def import_env(
    project: Optional[str], 
    env_file: str, 
    overwrite: bool, 
    strip_prefix: Optional[str],
    strip_suffix: Optional[str],
    add_prefix: Optional[str],
    add_suffix: Optional[str],
    description: Optional[str],
    preview: bool, 
    verbose: bool
):
    """Import environment variables from .env file into a project"""
    
    config = CLIConfig(verbose=verbose)
    
    if not project:
        project = config.default_project
        if not project:
            console.print("[red]Error: Project name is required. Use --project or set SECRETOOL_DEFAULT_PROJECT[/red]")
            return
    
    # Check if file exists
    env_path = Path(env_file)
    if not env_path.exists():
        console.print(f"[red]Error: File '{env_file}' not found[/red]")
        return
    
    if not env_path.is_file():
        console.print(f"[red]Error: '{env_file}' is not a file[/red]")
        return
    
    async def run_import():
        try:
            client = APIClient(config)
            
            # Check API health
            if verbose:
                console.print("🔍 Checking API health...")
            await client.health_check()
            
            # Get project by name
            if verbose:
                console.print(f"🔍 Looking up project: {project}")
            project_data = await client.get_project_by_name(project)
            if not project_data:
                console.print(f"[red]Error: Project '{project}' not found[/red]")
                return
            
            project_id = project_data["id"]
            if verbose:
                console.print(f"✅ Found project: {project} (ID: {project_id})")
            
            # Read .env file
            if verbose:
                console.print(f"📁 Reading file: {env_file}")
            
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    env_content = f.read()
            except Exception as e:
                console.print(f"[red]Error reading file: {e}[/red]")
                return
            
            # Prepare import request
            import_request = {
                "project_id": project_id,
                "env_content": env_content,
                "overwrite_existing": overwrite
            }
            
            # Add optional transformations
            if strip_prefix:
                import_request["strip_prefix"] = strip_prefix
            if strip_suffix:
                import_request["strip_suffix"] = strip_suffix
            if add_prefix:
                import_request["add_prefix"] = add_prefix
            if add_suffix:
                import_request["add_suffix"] = add_suffix
            if description:
                import_request["description"] = description
            
            if preview:
                # Preview import
                if verbose:
                    console.print("🔍 Generating import preview...")
                
                preview_result = await client.preview_env_import(import_request)
                
                # Display preview
                console.print(Panel(f"[bold]Import Preview for: {env_file}[/bold]"))
                
                # Summary
                console.print(f"📊 [bold]Summary[/bold]")
                console.print(f"   Total variables found: {preview_result['total_variables']}")
                console.print(f"   New variables: {len(preview_result['new_variables'])}")
                console.print(f"   Conflicts: {len(preview_result['conflicts'])}")
                console.print(f"   Skipped lines: {len(preview_result['skipped_lines'])}")
                
                # New variables
                if preview_result['new_variables']:
                    console.print(f"\n✅ [bold green]New Variables ({len(preview_result['new_variables'])})[/bold green]")
                    table = Table()
                    table.add_column("Name", style="cyan")
                    table.add_column("Value", style="green")
                    table.add_column("Line", style="yellow")
                    
                    for var in preview_result['new_variables']:
                        # Truncate long values
                        value = var['value']
                        if len(value) > 50:
                            value = value[:47] + "..."
                        table.add_row(var['name'], value, str(var['line_number']))
                    
                    console.print(table)
                
                # Conflicts
                if preview_result['conflicts']:
                    console.print(f"\n⚠️  [bold yellow]Conflicts ({len(preview_result['conflicts'])})[/bold yellow]")
                    table = Table()
                    table.add_column("Variable", style="cyan")
                    table.add_column("Existing Type", style="blue")
                    table.add_column("Existing Value", style="red")
                    table.add_column("New Value", style="green")
                    table.add_column("Action", style="yellow")
                    
                    for conflict in preview_result['conflicts']:
                        action = "Overwrite" if overwrite else "Skip"
                        existing_val = conflict['existing_value']
                        if existing_val and len(existing_val) > 30:
                            existing_val = existing_val[:27] + "..."
                        new_val = conflict['new_value']
                        if len(new_val) > 30:
                            new_val = new_val[:27] + "..."
                            
                        table.add_row(
                            conflict['variable_name'],
                            conflict['existing_type'],
                            existing_val or "None",
                            new_val,
                            action
                        )
                    
                    console.print(table)
                
                # Warnings
                if preview_result['warnings']:
                    console.print(f"\n⚠️  [bold orange1]Warnings[/bold orange1]")
                    for warning in preview_result['warnings']:
                        console.print(f"   • {warning}")
                
                # Skipped lines
                if preview_result['skipped_lines'] and verbose:
                    console.print(f"\n📝 [bold]Skipped Lines[/bold]")
                    for line in preview_result['skipped_lines'][:5]:  # Show first 5
                        console.print(f"   • {line}")
                    if len(preview_result['skipped_lines']) > 5:
                        console.print(f"   ... and {len(preview_result['skipped_lines']) - 5} more")
                
                console.print(f"\n[dim]Use [bold]--no-preview[/bold] to perform the actual import[/dim]")
                
            else:
                # Perform actual import
                if verbose:
                    console.print("🚀 Starting import...")
                
                result = await client.import_env_variables(import_request)
                
                if result['success']:
                    console.print(f"✅ [bold green]{result['message']}[/bold green]")
                    
                    # Show detailed results
                    if verbose or result['variables_imported'] > 0:
                        console.print(f"\n📊 [bold]Import Results[/bold]")
                        console.print(f"   Variables imported: {result['variables_imported']}")
                        console.print(f"   Variables skipped: {result['variables_skipped']}")
                        console.print(f"   Variables overwritten: {result['variables_overwritten']}")
                        console.print(f"   Conflicts resolved: {result['conflicts_resolved']}")
                        if result['import_id']:
                            console.print(f"   Import ID: {result['import_id']}")
                    
                    # Show warnings
                    if result['warnings']:
                        console.print(f"\n⚠️  [bold yellow]Warnings[/bold yellow]")
                        for warning in result['warnings']:
                            console.print(f"   • {warning}")
                else:
                    console.print(f"❌ [bold red]Import failed: {result['message']}[/bold red]")
                    
                    if result['errors']:
                        console.print(f"\n[bold red]Errors:[/bold red]")
                        for error in result['errors']:
                            console.print(f"   • {error}")
        
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            if verbose:
                import traceback
                console.print(traceback.format_exc())
    
    asyncio.run(run_import()) 