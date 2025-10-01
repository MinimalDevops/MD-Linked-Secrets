"""
Export command for secretool CLI.
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
@click.option("--project", "-p", help="Project name to export")
@click.option("--out-dir", "-o", default=".", help="Output directory for .env file")
@click.option("--prefix", help="Prefix to add to variable names")
@click.option("--suffix", help="Suffix to add to variable names")
@click.option("--dry-run", is_flag=True, help="Show what would be exported without writing files")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def export(project: Optional[str], out_dir: str, prefix: Optional[str], suffix: Optional[str], dry_run: bool, verbose: bool):
    """Export project variables to .env file"""
    
    config = CLIConfig(verbose=verbose)
    
    if not project:
        project = config.default_project
        if not project:
            console.print("[red]Error: Project name is required. Use --project or set SECRETOOL_DEFAULT_PROJECT[/red]")
            return
    
    async def run_export():
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
            
            # Resolve variables
            if verbose:
                console.print("🔍 Resolving variables...")
            resolved_vars = await client.resolve_variables(project_id=project_id)
            
            if not resolved_vars:
                console.print(f"[yellow]Warning: No variables found for project '{project}'[/yellow]")
                return
            
            # Prepare export path
            output_path = Path(out_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            env_file_path = output_path / config.env_file_name
            
            if verbose:
                console.print(f"📁 Output directory: {output_path.resolve()}")
                console.print(f"📄 Export file: {env_file_path.resolve()}")
            
            # Apply prefix/suffix if specified
            final_vars = {}
            for name, value in resolved_vars.items():
                final_name = name
                if prefix:
                    final_name = f"{prefix}{final_name}"
                if suffix:
                    final_name = f"{final_name}{suffix}"
                final_vars[final_name] = value
            
            # Generate .env content
            env_content = ""
            for name, value in final_vars.items():
                env_content += f"{name}={value}\n"
            
            if dry_run:
                # Show what would be exported
                console.print(Panel(f"[bold]DRY RUN - Would export to: {env_file_path}[/bold]"))
                
                table = Table(title=f"Variables for project '{project}'")
                table.add_column("Variable", style="cyan")
                table.add_column("Value", style="green")
                table.add_column("Type", style="yellow")
                
                for name, value in final_vars.items():
                    # Determine if this was modified by prefix/suffix
                    original_name = name
                    if prefix and name.startswith(prefix):
                        original_name = name[len(prefix):]
                    if suffix and name.endswith(suffix):
                        original_name = name[:-len(suffix)]
                    
                    var_type = "modified" if original_name != name else "original"
                    table.add_row(name, value, var_type)
                
                console.print(table)
                console.print(f"\n[green]Total variables: {len(final_vars)}[/green]")
                
            else:
                # Write the .env file
                env_file_path.write_text(env_content)
                
                # Export via API to track the export
                try:
                    export_result = await client.export_project(
                        project_id=project_id,
                        export_path=str(env_file_path),
                        with_prefix=bool(prefix),
                        with_suffix=bool(suffix),
                        prefix_value=prefix,
                        suffix_value=suffix
                    )
                    
                    console.print(f"✅ Exported {len(final_vars)} variables to: {env_file_path}")
                    console.print(f"📊 Export ID: {export_result.get('export_id')}")
                    console.print(f"🔗 API tracked export at: {export_result.get('export_path')}")
                    
                except Exception as e:
                    console.print(f"⚠️  File written but API tracking failed: {e}")
                    console.print(f"✅ Exported {len(final_vars)} variables to: {env_file_path}")
                
                if verbose:
                    console.print(f"\n[dim]Content preview:[/dim]")
                    console.print(Panel(env_content[:500] + "..." if len(env_content) > 500 else env_content))
        
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            if verbose:
                import traceback
                console.print(traceback.format_exc())
    
    asyncio.run(run_export()) 