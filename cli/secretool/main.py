"""
Main CLI entry point for secretool.
"""

import click
from rich.console import Console
from rich.panel import Panel

from .commands.export import export
from .commands.check_updates import check_updates
from .commands.diff import diff
from .commands.import_env import import_env
from .commands.exports import list_exports, remove_export, export_summary
from .config import get_config

console = Console()


@click.group()
@click.version_option(version="1.0.0", prog_name="lsec")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Quiet output")
@click.pass_context
def cli(ctx, verbose: bool, quiet: bool):
    """
    MD-Linked-Secrets CLI Tool (lsec)
    
    Manage and link environment variables across multiple projects.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Store configuration in context
    config = get_config()
    config.verbose = verbose
    config.quiet = quiet
    ctx.obj["config"] = config
    
    if not quiet:
        console.print(Panel(
            "[bold blue]MD-Linked-Secrets CLI[/bold blue]\n"
            "Manage and link environment variables across projects",
            title="🔐 lsec"
        ))


# Add commands to the CLI group
cli.add_command(export)
cli.add_command(check_updates)
cli.add_command(diff)
cli.add_command(import_env)

# Export management commands
cli.add_command(list_exports, name="list-exports")
cli.add_command(remove_export, name="remove-export")
cli.add_command(export_summary, name="export-summary")


@cli.command()
@click.pass_context
def status(ctx):
    """Show current status and configuration"""
    config = ctx.obj["config"]
    
    console.print(Panel(
        f"[bold]Configuration[/bold]\n"
        f"API URL: {config.api_base_url}\n"
        f"Default Project: {config.default_project or 'Not set'}\n"
        f"Output Directory: {config.default_output_dir}\n"
        f"Environment File: {config.env_file_name}\n"
        f"Verbose: {config.verbose}\n"
        f"Quiet: {config.quiet}",
        title="📊 Status"
    ))


@cli.command()
@click.pass_context
def projects(ctx):
    """List all available projects"""
    import asyncio
    from .api_client import APIClient
    
    config = ctx.obj["config"]
    
    async def list_projects():
        try:
            client = APIClient(config)
            projects = await client.get_projects()
            
            if not projects:
                console.print("[yellow]No projects found[/yellow]")
                return
            
            from rich.table import Table
            table = Table(title="Available Projects")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="blue")
            table.add_column("Description", style="green")
            table.add_column("Variables", style="yellow")
            
            for project in projects:
                # Get variable count for this project
                vars_data = await client.get_env_vars(project["id"])
                var_count = len(vars_data)
                
                table.add_row(
                    str(project["id"]),
                    project["name"],
                    project.get("description", ""),
                    str(var_count)
                )
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    asyncio.run(list_projects())


@cli.command()
@click.option("--project", "-p", help="Project name to show variables for")
@click.pass_context
def variables(ctx, project: str):
    """List environment variables for a project"""
    import asyncio
    from .api_client import APIClient
    
    config = ctx.obj["config"]
    
    if not project:
        project = config.default_project
        if not project:
            console.print("[red]Error: Project name is required. Use --project or set SECRETOOL_DEFAULT_PROJECT[/red]")
            return
    
    async def list_variables():
        try:
            client = APIClient(config)
            
            # Get project
            project_data = await client.get_project_by_name(project)
            if not project_data:
                console.print(f"[red]Error: Project '{project}' not found[/red]")
                return
            
            # Get variables
            vars_data = await client.get_env_vars(project_data["id"])
            
            if not vars_data:
                console.print(f"[yellow]No variables found for project '{project}'[/yellow]")
                return
            
            from rich.table import Table
            table = Table(title=f"Variables for project '{project}'")
            table.add_column("Name", style="cyan")
            table.add_column("Type", style="blue")
            table.add_column("Value/Reference", style="green")
            table.add_column("Description", style="yellow")
            
            for var in vars_data:
                value_type = var.get("value_type", "unknown")
                value_display = "N/A"
                
                if value_type == "raw":
                    value_display = var.get("raw_value", "")[:50]
                elif value_type == "linked":
                    value_display = var.get("linked_to", "")
                elif value_type == "concatenated":
                    value_display = var.get("concat_parts", "")
                
                if len(value_display) > 50:
                    value_display = value_display[:47] + "..."
                
                table.add_row(
                    var["name"],
                    value_type,
                    value_display,
                    var.get("description", "")
                )
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    asyncio.run(list_variables())


if __name__ == "__main__":
    cli() 