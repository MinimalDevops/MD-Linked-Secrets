"""
Diff command for secretool CLI.
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
@click.option("--export-id", "-e", required=True, type=int, help="Export ID to compare")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--show-unchanged", is_flag=True, help="Show unchanged variables")
def diff(export_id: int, verbose: bool, show_unchanged: bool):
    """Show variable-level diff between past export and current value"""
    
    config = CLIConfig(verbose=verbose)
    
    async def run_diff():
        try:
            client = APIClient(config)
            
            # Check API health
            if verbose:
                console.print("🔍 Checking API health...")
            await client.health_check()
            
            # Get export details
            if verbose:
                console.print(f"🔍 Getting export details for ID: {export_id}")
            exports = await client.get_exports()
            export_data = None
            for export in exports:
                if export.get("id") == export_id:
                    export_data = export
                    break
            
            if not export_data:
                console.print(f"[red]Error: Export with ID {export_id} not found[/red]")
                return
            
            # Get diff
            if verbose:
                console.print("🔍 Getting diff data...")
            diff_result = await client.get_export_diff(export_id)
            
            # Display export info
            console.print(Panel(f"[bold]Export Details[/bold]\n"
                              f"ID: {export_id}\n"
                              f"Path: {export_data.get('export_path', 'N/A')}\n"
                              f"Project: {export_data.get('project_id', 'N/A')}\n"
                              f"Exported: {export_data.get('exported_at', 'N/A')}"))
            
            # Display diff
            differences = diff_result.get("differences", [])
            total_differences = diff_result.get("total_differences", 0)
            
            if total_differences == 0:
                console.print("✅ No differences found - export is up to date!")
                return
            
            # Show differences
            if differences:
                console.print(f"\n[bold red]Differences Found ({total_differences})[/bold red]")
                
                table = Table(title="Variable Differences")
                table.add_column("Variable", style="cyan")
                table.add_column("Stored Value", style="red")
                table.add_column("Current Value", style="green")
                table.add_column("Status", style="yellow")
                
                for diff in differences:
                    stored_value = diff.get("stored_value", "")
                    current_value = diff.get("current_value", "")
                    status = diff.get("status", "modified")
                    
                    # Truncate long values for display
                    if len(stored_value) > 50:
                        stored_value = stored_value[:47] + "..."
                    if len(current_value) > 50:
                        current_value = current_value[:47] + "..."
                    
                    table.add_row(
                        diff.get("variable", "N/A"),
                        stored_value,
                        current_value,
                        status
                    )
                
                console.print(table)
            
            # Summary
            console.print(f"\n[bold]Summary:[/bold] {total_differences} differences found")
            
            # Suggest re-export if there are changes
            if differences:
                console.print(f"\n[bold yellow]To update this export, run:[/bold yellow]")
                console.print(f"[cyan]secretool export --project PROJECT_NAME --out-dir {export_data.get('export_path', 'PATH')}[/cyan]")
        
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            if verbose:
                import traceback
                console.print(traceback.format_exc())
    
    asyncio.run(run_diff()) 